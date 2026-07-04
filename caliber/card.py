"""Trust Card generation.

A Trust Card is a machine-readable credential that proves an agent's
calibration through accumulated evidence. It answers: "When this agent
says it's 80% confident, how often is it actually right?"
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from caliber.tracker import Prediction


# Confidence bucket boundaries — chosen from MY UNIVERSE calibration data.
# The 60-79% range is split into two buckets because that's where
# miscalibration concentrates.
def _norm_cdf(x: float) -> float:
    """Standard normal CDF using math.erfc (no scipy needed)."""
    return 0.5 * math.erfc(-x / math.sqrt(2))


def _binomial_pmf(k: int, n: int, p: float) -> float:
    """Binomial probability mass in log-space."""
    if p <= 0:
        return 1.0 if k == 0 else 0.0
    if p >= 1:
        return 1.0 if k == n else 0.0
    log_pmf = (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
        + k * math.log(p)
        + (n - k) * math.log1p(-p)
    )
    return math.exp(log_pmf)


def _exact_binomial_p_two_sided(k: int, n: int, p0: float) -> float:
    """Two-sided exact binomial p-value.

    Sums every outcome whose PMF is no larger than the observed outcome's PMF,
    matching the probability-ordering definition from NORTHSTAR.md.
    """
    observed = _binomial_pmf(k, n, p0)
    tolerance = observed * (1 + 1e-9)
    return min(
        1.0,
        sum(
            _binomial_pmf(i, n, p0)
            for i in range(n + 1)
            if _binomial_pmf(i, n, p0) <= tolerance
        ),
    )


def _murphy_decomposition(
    forecasts: list[float],
    outcomes: list[int],
) -> tuple[float, float, float, float]:
    """Brier score and exact Murphy decomposition."""
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


def _spiegelhalter_z(
    forecasts: list[float],
    outcomes: list[int],
) -> tuple[float, float] | None:
    """Spiegelhalter's Z and two-sided p-value."""
    variance = sum(f * (1 - f) for f in forecasts)
    if variance <= 0:
        return None
    z = sum(o - f for f, o in zip(forecasts, outcomes)) / math.sqrt(variance)
    p_two = 2 * (1 - _norm_cdf(abs(z)))
    return z, p_two


BUCKET_RANGES = [
    (0.50, 0.59, "50-59"),
    (0.60, 0.69, "60-69"),
    (0.70, 0.79, "70-79"),
    (0.80, 0.89, "80-89"),
    (0.90, 0.99, "90-99"),
]

WILSON_Z_95 = 1.959963984540054


def _wilson_ci(correct: int, n: int) -> Optional[tuple[float, float]]:
    """Wilson 95% confidence interval for a binomial proportion."""
    if n == 0:
        return None
    p_hat = correct / n
    z = WILSON_Z_95
    z2 = z * z
    denom = 1 + z2 / n
    center = (p_hat + z2 / (2 * n)) / denom
    margin = (
        z
        * math.sqrt((p_hat * (1 - p_hat) / n) + (z2 / (4 * n * n)))
        / denom
    )
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    if abs(lower) < 1e-15:
        lower = 0.0
    if abs(upper - 1.0) < 1e-15:
        upper = 1.0
    return (lower, upper)


@dataclass
class BucketStats:
    """Statistics for one confidence bucket."""

    label: str
    predictions: int
    correct: int
    mean_confidence: Optional[float] = None

    @property
    def accuracy(self) -> Optional[float]:
        if self.predictions == 0:
            return None
        return self.correct / self.predictions

    @property
    def expected_accuracy(self) -> float:
        """Expected accuracy from stated confidence.

        Trust Cards generated from prediction streams use the mean stated
        confidence inside the bucket. A midpoint fallback is retained for
        manually constructed BucketStats in tests and compatibility code.
        """
        if self.mean_confidence is not None:
            return self.mean_confidence
        low = int(self.label.split("-")[0]) / 100
        high = int(self.label.split("-")[1]) / 100
        return (low + high) / 2

    @property
    def calibration_gap(self) -> Optional[float]:
        """Difference between expected and actual accuracy.

        Positive = overconfident (accuracy < confidence).
        Negative = underconfident (accuracy > confidence).
        """
        if self.accuracy is None:
            return None
        return self.expected_accuracy - self.accuracy

    @property
    def ci95(self) -> Optional[tuple[float, float]]:
        """Wilson 95% confidence interval for bucket accuracy."""
        return _wilson_ci(self.correct, self.predictions)

    @property
    def significant(self) -> Optional[bool]:
        """Is the calibration gap statistically significant (p < 0.05)?

        Uses an exact two-sided binomial test. Returns None if insufficient
        data (< 5 predictions).
        """
        if self.predictions < 5 or self.accuracy is None:
            return None
        p0 = self.expected_accuracy
        p_value = _exact_binomial_p_two_sided(
            self.correct,
            self.predictions,
            p0,
        )
        return p_value < 0.05

    def to_dict(self) -> dict:
        d = {"predictions": self.predictions, "correct": self.correct}
        if self.mean_confidence is not None:
            d["mean_confidence"] = round(self.mean_confidence, 3)
        if self.accuracy is not None:
            d["accuracy"] = round(self.accuracy, 3)
            ci95 = self.ci95
            if ci95 is not None:
                d["ci95"] = [round(ci95[0], 3), round(ci95[1], 3)]
            d["calibration_gap"] = round(self.calibration_gap, 3)
            sig = self.significant
            if sig is not None:
                d["significant"] = sig
            if self.predictions < 5:
                d["insufficient_data"] = True
        return d


@dataclass
class DomainStats:
    """Statistics for one prediction domain."""

    domain: str
    predictions: int
    correct: int
    avg_confidence: float

    @property
    def accuracy(self) -> Optional[float]:
        if self.predictions == 0:
            return None
        return self.correct / self.predictions

    def to_dict(self) -> dict:
        d = {
            "predictions": self.predictions,
            "correct": self.correct,
            "avg_confidence": round(self.avg_confidence, 3),
        }
        if self.accuracy is not None:
            d["accuracy"] = round(self.accuracy, 3)
        return d


@dataclass
class AdaptiveBucketStats:
    """Statistics for one equal-mass adaptive confidence bucket."""

    index: int
    predictions: int
    correct: int
    min_confidence: float
    max_confidence: float
    mean_confidence: float

    @property
    def accuracy(self) -> Optional[float]:
        if self.predictions == 0:
            return None
        return self.correct / self.predictions

    @property
    def calibration_gap(self) -> Optional[float]:
        if self.accuracy is None:
            return None
        return self.mean_confidence - self.accuracy

    @property
    def ci95(self) -> Optional[tuple[float, float]]:
        return _wilson_ci(self.correct, self.predictions)

    def to_dict(self) -> dict:
        d = {
            "index": self.index,
            "predictions": self.predictions,
            "correct": self.correct,
            "confidence_range": [
                round(self.min_confidence, 3),
                round(self.max_confidence, 3),
            ],
            "mean_confidence": round(self.mean_confidence, 3),
        }
        if self.accuracy is not None:
            d["accuracy"] = round(self.accuracy, 3)
            ci95 = self.ci95
            if ci95 is not None:
                d["ci95"] = [round(ci95[0], 3), round(ci95[1], 3)]
            d["calibration_gap"] = round(self.calibration_gap, 3)
        return d


@dataclass
class TrustCard:
    """A verifiable trust credential for an AI agent.

    Generated from real prediction data. The card answers:
    - Overall: how accurate is this agent?
    - By confidence: when it says 80%, is it right 80% of the time?
    - By domain: where is it strong? Where is it weak?
    - Calibration: is it over- or under-confident?
    """

    agent_name: str
    generated: datetime
    version: str = "0.1"
    total_predictions: int = 0
    total_verified: int = 0
    overall_accuracy: Optional[float] = None
    mean_confidence: Optional[float] = None
    mean_calibration_gap: Optional[float] = None
    brier_score: Optional[float] = None
    reliability: Optional[float] = None
    resolution: Optional[float] = None
    uncertainty: Optional[float] = None
    calibration_z: Optional[float] = None
    calibration_p: Optional[float] = None
    confidence_buckets: dict[str, BucketStats] = field(default_factory=dict)
    adaptive_buckets: list[AdaptiveBucketStats] = field(default_factory=list)
    domains: dict[str, DomainStats] = field(default_factory=dict)
    danger_zones: list[str] = field(default_factory=list)
    strength_zones: list[str] = field(default_factory=list)

    @classmethod
    def from_predictions(
        cls, agent_name: str, predictions: list[Prediction]
    ) -> TrustCard:
        """Build a Trust Card from verified predictions."""
        verified = [p for p in predictions if p.outcome is not None]
        if not verified:
            return cls(
                agent_name=agent_name,
                generated=datetime.now(timezone.utc),
                total_predictions=len(predictions),
            )

        correct = sum(1 for p in verified if p.outcome)
        overall_accuracy = correct / len(verified)
        mean_confidence = sum(p.confidence for p in verified) / len(verified)
        forecasts = [p.confidence for p in verified]
        outcomes = [1 if p.outcome else 0 for p in verified]
        brier, reliability, resolution, uncertainty = _murphy_decomposition(
            forecasts,
            outcomes,
        )
        spiegelhalter = _spiegelhalter_z(forecasts, outcomes)
        calibration_z = spiegelhalter[0] if spiegelhalter is not None else None
        calibration_p = spiegelhalter[1] if spiegelhalter is not None else None

        # Build confidence buckets
        buckets: dict[str, BucketStats] = {}
        for low, high, label in BUCKET_RANGES:
            in_bucket = [p for p in verified if low <= p.confidence <= high]
            bucket_correct = sum(1 for p in in_bucket if p.outcome)
            bucket_mean_confidence = (
                sum(p.confidence for p in in_bucket) / len(in_bucket)
                if in_bucket
                else None
            )
            buckets[label] = BucketStats(
                label=label,
                predictions=len(in_bucket),
                correct=bucket_correct,
                mean_confidence=bucket_mean_confidence,
            )

        adaptive_buckets = _build_adaptive_buckets(verified)

        # Build domain stats
        domain_groups: dict[str, list[Prediction]] = {}
        for p in verified:
            domain_groups.setdefault(p.domain, []).append(p)

        domains: dict[str, DomainStats] = {}
        for domain, preds in sorted(domain_groups.items()):
            d_correct = sum(1 for p in preds if p.outcome)
            d_avg_conf = sum(p.confidence for p in preds) / len(preds)
            domains[domain] = DomainStats(
                domain=domain,
                predictions=len(preds),
                correct=d_correct,
                avg_confidence=d_avg_conf,
            )

        # Identify danger zones (overconfident) and strength zones (underconfident).
        # A zone requires both a large gap and a completed significant test.
        danger_zones = []
        strength_zones = []
        for label, bucket in buckets.items():
            if bucket.predictions >= 3 and bucket.calibration_gap is not None:
                sig = bucket.significant  # None if <5 predictions
                gap = bucket.calibration_gap
                if gap > 0.10:
                    # Overconfident: accuracy < expected.
                    # A zone requires evidence, not just an untestable gap.
                    if sig is True:
                        danger_zones.append(label)
                elif gap < -0.10:
                    # Underconfident: accuracy > expected.
                    if sig is True:
                        strength_zones.append(label)

        # Mean calibration gap (weighted by bucket size)
        weighted_gaps = []
        for bucket in buckets.values():
            if bucket.calibration_gap is not None and bucket.predictions > 0:
                weighted_gaps.extend(
                    [bucket.calibration_gap] * bucket.predictions
                )
        mean_gap = (
            sum(weighted_gaps) / len(weighted_gaps) if weighted_gaps else None
        )

        return cls(
            agent_name=agent_name,
            generated=datetime.now(timezone.utc),
            total_predictions=len(predictions),
            total_verified=len(verified),
            overall_accuracy=overall_accuracy,
            mean_confidence=mean_confidence,
            mean_calibration_gap=mean_gap,
            brier_score=brier,
            reliability=reliability,
            resolution=resolution,
            uncertainty=uncertainty,
            calibration_z=calibration_z,
            calibration_p=calibration_p,
            confidence_buckets=buckets,
            adaptive_buckets=adaptive_buckets,
            domains=domains,
            danger_zones=danger_zones,
            strength_zones=strength_zones,
        )

    def to_dict(self) -> dict:
        """Serialize to the Trust Card JSON format."""
        d: dict = {
            "trust_version": self.version,
            "agent_name": self.agent_name,
            "generated": self.generated.isoformat(),
            "calibration": {
                "total_predictions": self.total_predictions,
                "total_verified": self.total_verified,
            },
        }

        cal = d["calibration"]
        if self.overall_accuracy is not None:
            cal["overall_accuracy"] = round(self.overall_accuracy, 3)
        if self.mean_confidence is not None:
            cal["mean_confidence"] = round(self.mean_confidence, 3)
        if self.mean_calibration_gap is not None:
            cal["mean_calibration_gap"] = round(self.mean_calibration_gap, 3)
        if self.brier_score is not None:
            cal["brier_score"] = round(self.brier_score, 4)
            cal["reliability"] = round(self.reliability, 4)
            cal["resolution"] = round(self.resolution, 4)
            cal["uncertainty"] = round(self.uncertainty, 4)
        if self.calibration_z is not None and self.calibration_p is not None:
            cal["calibration_z"] = round(self.calibration_z, 4)
            cal["calibration_p"] = round(self.calibration_p, 4)

        if self.confidence_buckets:
            cal["confidence_buckets"] = {
                label: bucket.to_dict()
                for label, bucket in self.confidence_buckets.items()
            }

        if self.adaptive_buckets:
            cal["adaptive_buckets"] = [
                bucket.to_dict() for bucket in self.adaptive_buckets
            ]

        if self.domains:
            cal["domains"] = {
                name: stats.to_dict() for name, stats in self.domains.items()
            }

        if self.danger_zones:
            cal["danger_zones"] = self.danger_zones
        if self.strength_zones:
            cal["strength_zones"] = self.strength_zones

        return d

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def summary(self) -> str:
        """Human-readable summary of the Trust Card."""
        lines = [
            f"Trust Card: {self.agent_name}",
            f"Generated: {self.generated.strftime('%Y-%m-%d %H:%M UTC')}",
            f"Predictions: {self.total_verified} verified / {self.total_predictions} total",
        ]

        if self.overall_accuracy is not None:
            lines.append(
                f"Overall accuracy: {self.overall_accuracy:.1%}"
            )
        if self.mean_confidence is not None:
            lines.append(
                f"Mean confidence: {self.mean_confidence:.1%}"
            )
        if self.mean_calibration_gap is not None:
            direction = "overconfident" if self.mean_calibration_gap > 0 else "underconfident"
            lines.append(
                f"Calibration gap: {abs(self.mean_calibration_gap):.1%} ({direction})"
            )
        if self.brier_score is not None:
            lines.append(
                f"Brier score: {self.brier_score:.4f} "
                f"(reliability {self.reliability:.4f} - "
                f"resolution {self.resolution:.4f} + "
                f"uncertainty {self.uncertainty:.4f})"
            )
        if self.calibration_z is not None and self.calibration_p is not None:
            lines.append(
                f"Calibration Z: {self.calibration_z:.3f} "
                f"(p={self.calibration_p:.3f})"
            )

        if self.confidence_buckets:
            lines.append("\nConfidence buckets:")
            for label, bucket in self.confidence_buckets.items():
                if bucket.predictions > 0:
                    marker = ""
                    if label in self.danger_zones:
                        marker = " ⚠ DANGER"
                    elif label in self.strength_zones:
                        marker = " ✓ STRENGTH"
                    sig_note = ""
                    if bucket.predictions < 5:
                        sig_note = " [insufficient data]"
                    elif bucket.significant is False:
                        sig_note = " [not significant]"
                    ci95 = bucket.ci95
                    ci_note = (
                        f", 95% CI {ci95[0]:.1%}-{ci95[1]:.1%}"
                        if ci95 is not None
                        else ""
                    )
                    lines.append(
                        f"  {label}%: {bucket.accuracy:.1%} accurate "
                        f"({bucket.predictions} predictions{ci_note})"
                        f"{marker}{sig_note}"
                    )

        if self.adaptive_buckets:
            lines.append("\nAdaptive buckets:")
            for bucket in self.adaptive_buckets:
                ci95 = bucket.ci95
                ci_note = (
                    f", 95% CI {ci95[0]:.1%}-{ci95[1]:.1%}"
                    if ci95 is not None
                    else ""
                )
                lines.append(
                    f"  #{bucket.index}: {bucket.accuracy:.1%} accurate "
                    f"({bucket.predictions} predictions, "
                    f"conf {bucket.min_confidence:.0%}-{bucket.max_confidence:.0%}, "
                    f"mean {bucket.mean_confidence:.1%}{ci_note})"
                )

        if self.domains:
            lines.append("\nDomains:")
            for name, stats in self.domains.items():
                lines.append(
                    f"  {name}: {stats.accuracy:.1%} accurate "
                    f"({stats.predictions} predictions, "
                    f"avg confidence {stats.avg_confidence:.0%})"
                )

        if self.danger_zones:
            lines.append(
                f"\nDanger zones: {', '.join(f'{z}%' for z in self.danger_zones)}"
            )
        if self.strength_zones:
            lines.append(
                f"Strength zones: {', '.join(f'{z}%' for z in self.strength_zones)}"
            )

        return "\n".join(lines)


def _build_adaptive_buckets(predictions: list[Prediction]) -> list[AdaptiveBucketStats]:
    """Build near-equal-count buckets sorted by confidence."""
    n = len(predictions)
    if n == 0:
        return []
    bucket_count = min(n, max(3, math.ceil(n / 25)))
    ordered = sorted(predictions, key=lambda p: p.confidence)
    buckets: list[AdaptiveBucketStats] = []
    for i in range(bucket_count):
        start = i * n // bucket_count
        end = (i + 1) * n // bucket_count
        group = ordered[start:end]
        correct = sum(1 for p in group if p.outcome)
        confidences = [p.confidence for p in group]
        buckets.append(
            AdaptiveBucketStats(
                index=i + 1,
                predictions=len(group),
                correct=correct,
                min_confidence=min(confidences),
                max_confidence=max(confidences),
                mean_confidence=sum(confidences) / len(confidences),
            )
        )
    return buckets
