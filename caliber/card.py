"""Trust Card generation.

A Trust Card is a machine-readable credential that proves an agent's
calibration through accumulated evidence. It answers: "When this agent
says it's 80% confident, how often is it actually right?"
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from caliber.tracker import Prediction


# Confidence bucket boundaries — chosen from MY UNIVERSE calibration data.
# The 60-79% range is split into two buckets because that's where
# miscalibration concentrates.
BUCKET_RANGES = [
    (0.50, 0.59, "50-59"),
    (0.60, 0.69, "60-69"),
    (0.70, 0.79, "70-79"),
    (0.80, 0.89, "80-89"),
    (0.90, 0.99, "90-99"),
]


@dataclass
class BucketStats:
    """Statistics for one confidence bucket."""

    label: str
    predictions: int
    correct: int

    @property
    def accuracy(self) -> Optional[float]:
        if self.predictions == 0:
            return None
        return self.correct / self.predictions

    @property
    def expected_accuracy(self) -> float:
        """Midpoint of the bucket range — what accuracy should be."""
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

    def to_dict(self) -> dict:
        d = {"predictions": self.predictions, "correct": self.correct}
        if self.accuracy is not None:
            d["accuracy"] = round(self.accuracy, 3)
            d["calibration_gap"] = round(self.calibration_gap, 3)
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
    confidence_buckets: dict[str, BucketStats] = field(default_factory=dict)
    domains: dict[str, DomainStats] = field(default_factory=dict)
    danger_zones: list[str] = field(default_factory=list)

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

        # Build confidence buckets
        buckets: dict[str, BucketStats] = {}
        for low, high, label in BUCKET_RANGES:
            in_bucket = [p for p in verified if low <= p.confidence <= high]
            bucket_correct = sum(1 for p in in_bucket if p.outcome)
            buckets[label] = BucketStats(
                label=label,
                predictions=len(in_bucket),
                correct=bucket_correct,
            )

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

        # Identify danger zones — buckets where accuracy < expected - 0.10
        # (more than 10 percentage points worse than confidence implies)
        danger_zones = []
        for label, bucket in buckets.items():
            if bucket.predictions >= 3 and bucket.calibration_gap is not None:
                if bucket.calibration_gap > 0.10:
                    danger_zones.append(label)

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
            confidence_buckets=buckets,
            domains=domains,
            danger_zones=danger_zones,
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

        if self.confidence_buckets:
            cal["confidence_buckets"] = {
                label: bucket.to_dict()
                for label, bucket in self.confidence_buckets.items()
            }

        if self.domains:
            cal["domains"] = {
                name: stats.to_dict() for name, stats in self.domains.items()
            }

        if self.danger_zones:
            cal["danger_zones"] = self.danger_zones

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

        if self.confidence_buckets:
            lines.append("\nConfidence buckets:")
            for label, bucket in self.confidence_buckets.items():
                if bucket.predictions > 0:
                    marker = " ⚠" if label in self.danger_zones else ""
                    lines.append(
                        f"  {label}%: {bucket.accuracy:.1%} accurate "
                        f"({bucket.predictions} predictions){marker}"
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

        return "\n".join(lines)
