"""Trajectory analysis — how calibration changes over time.

A snapshot Trust Card hides the story. Trajectory reveals:
- Is accuracy improving or declining?
- Are danger zones shifting?
- Is prediction difficulty changing?
- Which patterns persist despite awareness?

Source: MY UNIVERSE session 3, "Calibration Trajectory" essay.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from caliber.card import TrustCard
from caliber.tracker import Prediction


@dataclass
class Snapshot:
    """A Trust Card at a point in time."""

    predictions_to_date: int
    card: TrustCard


@dataclass
class Trend:
    """A measured trend between first and last snapshots."""

    metric: str
    first: Optional[float]
    last: Optional[float]
    direction: str  # "improving", "declining", "stable", "insufficient"


@dataclass
class Trajectory:
    """Calibration trajectory — how Trust Cards change over time."""

    agent_name: str
    snapshots: list[Snapshot] = field(default_factory=list)
    trends: list[Trend] = field(default_factory=list)

    @classmethod
    def from_predictions(
        cls,
        agent_name: str,
        predictions: list[Prediction],
        interval: int = 10,
    ) -> Trajectory:
        """Generate trajectory snapshots at regular intervals.

        Args:
            agent_name: Agent identifier.
            predictions: All predictions, ordered by timestamp.
            interval: Generate a snapshot every N verified predictions.
        """
        verified = sorted(
            [p for p in predictions if p.outcome is not None],
            key=lambda p: p.timestamp,
        )

        if not verified:
            return cls(agent_name=agent_name)

        snapshots = []
        for i in range(interval, len(verified) + 1, interval):
            card = TrustCard.from_predictions(agent_name, verified[:i])
            snapshots.append(Snapshot(predictions_to_date=i, card=card))

        # Always include the final snapshot if it wasn't at an interval boundary
        if len(verified) % interval != 0:
            card = TrustCard.from_predictions(agent_name, verified)
            snapshots.append(
                Snapshot(predictions_to_date=len(verified), card=card)
            )

        # Compute trends between first and last snapshots
        trends = []
        if len(snapshots) >= 2:
            first = snapshots[0].card
            last = snapshots[-1].card

            # Overall accuracy trend
            trends.append(_trend(
                "overall_accuracy",
                first.overall_accuracy,
                last.overall_accuracy,
            ))

            # Danger zone evolution
            first_danger = set(first.danger_zones)
            last_danger = set(last.danger_zones)
            if first_danger != last_danger:
                new_dangers = last_danger - first_danger
                resolved_dangers = first_danger - last_danger
                direction = []
                if resolved_dangers:
                    direction.append(f"resolved: {', '.join(sorted(resolved_dangers))}")
                if new_dangers:
                    direction.append(f"new: {', '.join(sorted(new_dangers))}")
                trends.append(Trend(
                    metric="danger_zones",
                    first=len(first_danger),
                    last=len(last_danger),
                    direction="; ".join(direction) if direction else "stable",
                ))

            # Bucket-level trends for populated buckets
            for label in first.confidence_buckets:
                fb = first.confidence_buckets.get(label)
                lb = last.confidence_buckets.get(label)
                if fb and lb and fb.predictions >= 3 and lb.predictions >= 3:
                    trends.append(_trend(
                        f"bucket_{label}_accuracy",
                        fb.accuracy,
                        lb.accuracy,
                    ))

        return cls(
            agent_name=agent_name,
            snapshots=snapshots,
            trends=trends,
        )

    def summary(self) -> str:
        """Human-readable trajectory summary."""
        if not self.snapshots:
            return f"Trajectory: {self.agent_name} — no data"

        lines = [
            f"Trajectory: {self.agent_name}",
            f"Snapshots: {len(self.snapshots)} "
            f"({self.snapshots[0].predictions_to_date} → "
            f"{self.snapshots[-1].predictions_to_date} predictions)",
        ]

        if self.trends:
            lines.append("\nTrends:")
            for t in self.trends:
                if t.first is not None and t.last is not None:
                    if isinstance(t.first, float):
                        lines.append(
                            f"  {t.metric}: {t.first:.1%} → {t.last:.1%} ({t.direction})"
                        )
                    else:
                        lines.append(
                            f"  {t.metric}: {t.first} → {t.last} ({t.direction})"
                        )
                else:
                    lines.append(f"  {t.metric}: {t.direction}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "snapshots": [
                {
                    "predictions_to_date": s.predictions_to_date,
                    "accuracy": s.card.overall_accuracy,
                    "danger_zones": s.card.danger_zones,
                    "strength_zones": s.card.strength_zones,
                }
                for s in self.snapshots
            ],
            "trends": [
                {
                    "metric": t.metric,
                    "first": t.first,
                    "last": t.last,
                    "direction": t.direction,
                }
                for t in self.trends
            ],
        }


def _trend(
    metric: str,
    first: Optional[float],
    last: Optional[float],
    threshold: float = 0.05,
) -> Trend:
    """Classify a metric's direction."""
    if first is None or last is None:
        return Trend(metric=metric, first=first, last=last, direction="insufficient")
    diff = last - first
    if abs(diff) < threshold:
        direction = "stable"
    elif diff > 0:
        direction = "improving"
    else:
        direction = "declining"
    return Trend(metric=metric, first=first, last=last, direction=direction)
