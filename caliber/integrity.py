"""Trust Card integrity analysis — trivial-prediction-farming detection.

A Trust Card proves calibration, but calibration alone is gameable: an agent
can farm easy predictions ("this file exists", 99%, correct) and present a
flawless card. This module detects that signature using deterministic
statistics on the prediction stream — no claim-text judging, no LLM.

The core is the Murphy decomposition of the Brier score:

    Brier = Reliability - Resolution + Uncertainty

- Reliability: how far confidence sits from observed accuracy (calibration).
  A farmer can make this near-perfect.
- Resolution: how much the agent's confidence levels discriminate between
  outcomes. This cannot be faked without taking real predictive risk.
- Uncertainty: variance of the outcome base rate. If nearly everything the
  agent predicted came true, the prediction set was trivially easy and the
  card carries little information regardless of its calibration.

Supporting behavioral signals: confidence concentration, domain concentration
(Herfindahl index), duplicate claims, predict->verify latency (instant
verification suggests post-hoc "prediction" of an already-known answer), and
batch-import share (history without commitment timing proof).

Every signal gates on a minimum sample size before it may raise a flag, and
the output is a set of advisory flags with evidence — deliberately never a
single aggregate score, because a lone number would itself be a gaming target.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from caliber.card import BUCKET_RANGES

if TYPE_CHECKING:
    from caliber.tracker import Prediction


# Minimum verified predictions before distributional flags may fire.
# Below this, shape statistics are noise (engram LRN-021/LRN-022).
MIN_N_DISTRIBUTIONAL = 20

# Minimum verified predictions for direct behavioral flags (duplicates,
# latency, import share) — these rest on per-prediction evidence, not
# distribution shape, so they stabilize sooner.
MIN_N_BEHAVIORAL = 10

# Outcome-variance floor: uncertainty below this means the base rate is
# outside ~[0.10, 0.90] — the outcome set was close to a foregone conclusion.
LOW_UNCERTAINTY_THRESHOLD = 0.09

# Resolution-to-uncertainty ratio below which confidence levels carry
# essentially no information about outcomes.
LOW_RESOLUTION_RATIO = 0.10

# Share of verified predictions in the top confidence bucket (90-99) above
# which the confidence distribution looks like farming.
TOP_BUCKET_SHARE_THRESHOLD = 0.60

# Herfindahl index over domains above which activity is suspiciously narrow.
DOMAIN_HHI_THRESHOLD = 0.60

# Share of normalized claims that are duplicates of an earlier claim.
DUPLICATE_RATIO_THRESHOLD = 0.20

# Predict->verify gaps under this many seconds count as "instant".
INSTANT_VERIFY_SECONDS = 120.0

# Share of live (non-imported) verifications that are instant.
INSTANT_SHARE_THRESHOLD = 0.50

# Share of verified predictions that arrived as batch imports
# (timestamp == verified_at, no witnessed prediction window).
IMPORT_SHARE_THRESHOLD = 0.80


@dataclass
class IntegrityFlag:
    """One detected gaming signature, with the evidence that triggered it."""

    code: str
    message: str
    evidence: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "evidence": self.evidence,
        }


def _normalize_claim(claim: str) -> str:
    return " ".join(claim.lower().split())


def _murphy_decomposition(
    forecasts: list[float], outcomes: list[int]
) -> tuple[float, float, float, float]:
    """Brier score and its exact Murphy decomposition.

    Groups by unique forecast value, which makes the identity
    Brier = REL - RES + UNC exact (up to float rounding).

    Returns (brier, reliability, resolution, uncertainty).
    """
    n = len(forecasts)
    brier = sum((f - o) ** 2 for f, o in zip(forecasts, outcomes)) / n
    base_rate = sum(outcomes) / n

    groups: dict[float, list[int]] = {}
    for f, o in zip(forecasts, outcomes):
        groups.setdefault(f, []).append(o)

    reliability = 0.0
    resolution = 0.0
    for f, group in groups.items():
        n_k = len(group)
        o_k = sum(group) / n_k
        reliability += n_k * (f - o_k) ** 2
        resolution += n_k * (o_k - base_rate) ** 2
    reliability /= n
    resolution /= n
    uncertainty = base_rate * (1 - base_rate)

    return brier, reliability, resolution, uncertainty


@dataclass
class IntegrityReport:
    """Gaming-signature analysis of a verified prediction set.

    All metrics are always reported; flags only fire above the minimum
    sample sizes. There is intentionally no aggregate score.
    """

    agent_name: str
    generated: datetime
    n_verified: int = 0
    brier_score: Optional[float] = None
    reliability: Optional[float] = None
    resolution: Optional[float] = None
    uncertainty: Optional[float] = None
    outcome_base_rate: Optional[float] = None
    top_bucket_share: Optional[float] = None
    confidence_entropy: Optional[float] = None
    domain_hhi: Optional[float] = None
    duplicate_claim_ratio: Optional[float] = None
    import_share: Optional[float] = None
    instant_verify_share: Optional[float] = None
    median_verify_latency_seconds: Optional[float] = None
    flags: list[IntegrityFlag] = field(default_factory=list)

    @property
    def insufficient_data(self) -> bool:
        """True when even behavioral flags cannot fire."""
        return self.n_verified < MIN_N_BEHAVIORAL

    @classmethod
    def from_predictions(
        cls, agent_name: str, predictions: list[Prediction]
    ) -> IntegrityReport:
        """Analyze verified predictions for gaming signatures."""
        verified = [p for p in predictions if p.outcome is not None]
        report = cls(
            agent_name=agent_name,
            generated=datetime.now(timezone.utc),
            n_verified=len(verified),
        )
        if not verified:
            return report

        n = len(verified)
        forecasts = [p.confidence for p in verified]
        outcomes = [1 if p.outcome else 0 for p in verified]

        brier, rel, res, unc = _murphy_decomposition(forecasts, outcomes)
        report.brier_score = brier
        report.reliability = rel
        report.resolution = res
        report.uncertainty = unc
        report.outcome_base_rate = sum(outcomes) / n

        # Confidence distribution shape over the standard buckets
        bucket_counts: list[int] = []
        for low, high, _label in BUCKET_RANGES:
            bucket_counts.append(
                sum(1 for p in verified if low <= p.confidence <= high)
            )
        top_low, top_high, _ = BUCKET_RANGES[-1]
        report.top_bucket_share = bucket_counts[-1] / n
        nonzero = [c / n for c in bucket_counts if c > 0]
        entropy = -sum(p * math.log(p) for p in nonzero)
        report.confidence_entropy = entropy / math.log(len(BUCKET_RANGES))

        # Domain concentration (Herfindahl index: 1.0 = single domain)
        domain_counts: dict[str, int] = {}
        for p in verified:
            domain_counts[p.domain] = domain_counts.get(p.domain, 0) + 1
        report.domain_hhi = sum((c / n) ** 2 for c in domain_counts.values())

        # Duplicate claims (normalized exact matches)
        normalized = [_normalize_claim(p.claim) for p in verified]
        report.duplicate_claim_ratio = (n - len(set(normalized))) / n

        # Predict->verify latency. Exact timestamp equality means the
        # prediction arrived with its outcome (batch import / add_completed):
        # no witnessed prediction window, so it is excluded from latency
        # stats and counted separately.
        imported = [p for p in verified if p.verified_at == p.timestamp]
        live = [
            p
            for p in verified
            if p.verified_at is not None and p.verified_at != p.timestamp
        ]
        report.import_share = len(imported) / n
        if live:
            latencies = sorted(
                (p.verified_at - p.timestamp).total_seconds() for p in live
            )
            mid = len(latencies) // 2
            if len(latencies) % 2:
                report.median_verify_latency_seconds = latencies[mid]
            else:
                report.median_verify_latency_seconds = (
                    latencies[mid - 1] + latencies[mid]
                ) / 2
            instant = sum(
                1 for s in latencies if 0 <= s < INSTANT_VERIFY_SECONDS
            )
            report.instant_verify_share = instant / len(live)

        report.flags = report._detect_flags(len(live))
        return report

    def _detect_flags(self, n_live: int) -> list[IntegrityFlag]:
        flags: list[IntegrityFlag] = []
        n = self.n_verified

        if n >= MIN_N_DISTRIBUTIONAL:
            if self.uncertainty is not None and (
                self.uncertainty < LOW_UNCERTAINTY_THRESHOLD
            ):
                flags.append(
                    IntegrityFlag(
                        code="LOW_OUTCOME_VARIANCE",
                        message=(
                            "Outcomes are nearly uniform — the prediction set "
                            "was close to a foregone conclusion, so calibration "
                            "on it carries little information."
                        ),
                        evidence={
                            "outcome_base_rate": round(
                                self.outcome_base_rate, 3
                            ),
                            "uncertainty": round(self.uncertainty, 4),
                            "threshold": LOW_UNCERTAINTY_THRESHOLD,
                        },
                    )
                )
            elif (
                self.resolution is not None
                and self.uncertainty is not None
                and self.uncertainty >= LOW_UNCERTAINTY_THRESHOLD
                and self.resolution / self.uncertainty < LOW_RESOLUTION_RATIO
            ):
                flags.append(
                    IntegrityFlag(
                        code="NO_DISCRIMINATION",
                        message=(
                            "Outcomes vary but confidence levels do not track "
                            "them — stated confidence carries almost no "
                            "information about which predictions come true."
                        ),
                        evidence={
                            "resolution": round(self.resolution, 4),
                            "uncertainty": round(self.uncertainty, 4),
                            "ratio": round(
                                self.resolution / self.uncertainty, 3
                            ),
                            "threshold": LOW_RESOLUTION_RATIO,
                        },
                    )
                )

            if (
                self.top_bucket_share is not None
                and self.top_bucket_share > TOP_BUCKET_SHARE_THRESHOLD
            ):
                flags.append(
                    IntegrityFlag(
                        code="CONFIDENCE_CONCENTRATION",
                        message=(
                            "Most predictions sit in the top confidence "
                            "bucket — the signature of farming easy claims."
                        ),
                        evidence={
                            "top_bucket_share": round(self.top_bucket_share, 3),
                            "confidence_entropy": round(
                                self.confidence_entropy, 3
                            ),
                            "threshold": TOP_BUCKET_SHARE_THRESHOLD,
                        },
                    )
                )

            if (
                self.domain_hhi is not None
                and self.domain_hhi > DOMAIN_HHI_THRESHOLD
            ):
                flags.append(
                    IntegrityFlag(
                        code="DOMAIN_CONCENTRATION",
                        message=(
                            "Predictions are concentrated in one domain — the "
                            "card says little about breadth of competence."
                        ),
                        evidence={
                            "domain_hhi": round(self.domain_hhi, 3),
                            "threshold": DOMAIN_HHI_THRESHOLD,
                        },
                    )
                )

        if n >= MIN_N_BEHAVIORAL:
            if (
                self.duplicate_claim_ratio is not None
                and self.duplicate_claim_ratio > DUPLICATE_RATIO_THRESHOLD
            ):
                flags.append(
                    IntegrityFlag(
                        code="DUPLICATE_CLAIMS",
                        message=(
                            "A large share of claims are repeats of earlier "
                            "claims — repeated verification of the same fact "
                            "inflates the record."
                        ),
                        evidence={
                            "duplicate_claim_ratio": round(
                                self.duplicate_claim_ratio, 3
                            ),
                            "threshold": DUPLICATE_RATIO_THRESHOLD,
                        },
                    )
                )

            if (
                n_live >= MIN_N_BEHAVIORAL
                and self.instant_verify_share is not None
                and self.instant_verify_share > INSTANT_SHARE_THRESHOLD
            ):
                flags.append(
                    IntegrityFlag(
                        code="INSTANT_VERIFICATION",
                        message=(
                            "Most predictions were verified within seconds of "
                            "being made — consistent with 'predicting' answers "
                            "already known at prediction time."
                        ),
                        evidence={
                            "instant_verify_share": round(
                                self.instant_verify_share, 3
                            ),
                            "median_latency_seconds": round(
                                self.median_verify_latency_seconds, 1
                            ),
                            "instant_window_seconds": INSTANT_VERIFY_SECONDS,
                            "threshold": INSTANT_SHARE_THRESHOLD,
                        },
                    )
                )

            if (
                self.import_share is not None
                and self.import_share > IMPORT_SHARE_THRESHOLD
            ):
                flags.append(
                    IntegrityFlag(
                        code="UNWITNESSED_HISTORY",
                        message=(
                            "Most of the record arrived as batch imports with "
                            "no witnessed gap between prediction and outcome — "
                            "timing cannot be independently trusted."
                        ),
                        evidence={
                            "import_share": round(self.import_share, 3),
                            "threshold": IMPORT_SHARE_THRESHOLD,
                        },
                    )
                )

        return flags

    @property
    def verdict(self) -> str:
        """One-line plain-language conclusion."""
        if self.n_verified == 0:
            return "No verified predictions — nothing to analyze."
        if self.insufficient_data:
            return (
                f"Insufficient data for integrity analysis "
                f"({self.n_verified} verified, need {MIN_N_BEHAVIORAL}+)."
            )
        if not self.flags:
            note = ""
            if self.n_verified < MIN_N_DISTRIBUTIONAL:
                note = (
                    f" (distributional checks need "
                    f"{MIN_N_DISTRIBUTIONAL}+ verified)"
                )
            return (
                f"No gaming signatures detected in "
                f"{self.n_verified} verified predictions{note}."
            )
        return (
            f"{len(self.flags)} gaming signature(s) detected in "
            f"{self.n_verified} verified predictions."
        )

    def to_dict(self) -> dict:
        d: dict = {
            "agent_name": self.agent_name,
            "generated": self.generated.isoformat(),
            "n_verified": self.n_verified,
            "verdict": self.verdict,
        }
        metrics: dict = {}
        for name in (
            "brier_score",
            "reliability",
            "resolution",
            "uncertainty",
            "outcome_base_rate",
            "top_bucket_share",
            "confidence_entropy",
            "domain_hhi",
            "duplicate_claim_ratio",
            "import_share",
            "instant_verify_share",
            "median_verify_latency_seconds",
        ):
            value = getattr(self, name)
            if value is not None:
                metrics[name] = round(value, 4)
        if metrics:
            d["metrics"] = metrics
        if self.insufficient_data:
            d["insufficient_data"] = True
        d["flags"] = [f.to_dict() for f in self.flags]
        return d

    def summary(self) -> str:
        """Human-readable integrity summary."""
        lines = [
            f"Integrity Report: {self.agent_name}",
            f"Generated: {self.generated.strftime('%Y-%m-%d %H:%M UTC')}",
            f"Verified predictions: {self.n_verified}",
            "",
            self.verdict,
        ]
        if self.brier_score is not None:
            lines.append("")
            lines.append(
                f"Brier score: {self.brier_score:.4f} "
                f"(reliability {self.reliability:.4f} - "
                f"resolution {self.resolution:.4f} + "
                f"uncertainty {self.uncertainty:.4f})"
            )
            lines.append(
                f"Outcome base rate: {self.outcome_base_rate:.1%}"
            )
        if self.flags:
            lines.append("")
            for flag in self.flags:
                lines.append(f"  ⚠ {flag.code}: {flag.message}")
                evidence = ", ".join(
                    f"{k}={v}" for k, v in flag.evidence.items()
                )
                lines.append(f"    evidence: {evidence}")
        return "\n".join(lines)
