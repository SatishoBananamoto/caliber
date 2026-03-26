"""Core prediction tracking for caliber.

The tracker records predictions with confidence levels and outcomes,
building the calibration data that Trust Cards are generated from.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from caliber.storage import Storage, FileStorage


@dataclass
class Prediction:
    """A single prediction with confidence and outcome."""

    id: str
    claim: str
    confidence: float  # 0.50 to 0.99
    domain: str
    timestamp: datetime
    outcome: Optional[bool] = None  # True=correct, False=incorrect, None=unverified
    verified_at: Optional[datetime] = None
    notes: Optional[str] = None
    commitment_hash: Optional[str] = None
    commitment_salt: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "claim": self.claim,
            "confidence": self.confidence,
            "domain": self.domain,
            "timestamp": self.timestamp.isoformat(),
            "outcome": self.outcome,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "notes": self.notes,
        }
        if self.commitment_hash:
            d["commitment_hash"] = self.commitment_hash
            d["commitment_salt"] = self.commitment_salt
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Prediction:
        return cls(
            id=data["id"],
            claim=data["claim"],
            confidence=data["confidence"],
            domain=data["domain"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            outcome=data.get("outcome"),
            commitment_hash=data.get("commitment_hash"),
            commitment_salt=data.get("commitment_salt"),
            verified_at=(
                datetime.fromisoformat(data["verified_at"])
                if data.get("verified_at")
                else None
            ),
            notes=data.get("notes"),
        )


def _validate_confidence(confidence: float) -> float:
    """Validate and clamp confidence to [0.50, 0.99]."""
    if not isinstance(confidence, (int, float)):
        raise TypeError(f"confidence must be a number, got {type(confidence).__name__}")
    confidence = float(confidence)
    if confidence < 0.50 or confidence > 0.99:
        raise ValueError(
            f"confidence must be between 0.50 and 0.99, got {confidence}"
        )
    return confidence


class TrustTracker:
    """Tracks predictions and outcomes for an agent.

    Usage:
        tracker = TrustTracker("my-agent")
        pid = tracker.predict("this file has >200 lines", confidence=0.85, domain="codebase")
        tracker.verify(pid, correct=True)
        card = tracker.generate_card()
    """

    def __init__(
        self,
        agent_name: str,
        storage: Optional[Storage] = None,
        store_path: Optional[str] = None,
        signed: bool = False,
    ):
        self.agent_name = agent_name
        self.signed = signed
        self._predictions: dict[str, Prediction] = {}

        if storage is not None:
            self._storage = storage
        elif store_path is not None:
            self._storage = FileStorage(store_path)
        else:
            self._storage = None

        # Load existing predictions from storage
        if self._storage is not None:
            for p in self._storage.load(agent_name):
                self._predictions[p.id] = p

    def predict(
        self,
        claim: str,
        confidence: float,
        domain: str,
        timestamp: Optional[datetime] = None,
        prediction_id: Optional[str] = None,
    ) -> str:
        """Record a prediction before verification.

        Args:
            claim: What you expect to find.
            confidence: How confident (0.50–0.99).
            domain: Category (e.g. "codebase", "behavior", "architecture").
            timestamp: When the prediction was made. Defaults to now.
            prediction_id: Optional explicit ID. Auto-generated if omitted.

        Returns:
            The prediction ID for later verification.
        """
        confidence = _validate_confidence(confidence)

        pid = prediction_id or uuid.uuid4().hex[:8]
        ts = timestamp or datetime.now(timezone.utc)

        commitment_hash = None
        commitment_salt = None
        if self.signed:
            from caliber.commitment import create_commitment
            c = create_commitment(claim, confidence, domain, ts)
            commitment_hash = c.commitment_hash
            commitment_salt = c.salt

        pred = Prediction(
            id=pid,
            claim=claim,
            confidence=confidence,
            domain=domain,
            timestamp=ts,
            commitment_hash=commitment_hash,
            commitment_salt=commitment_salt,
        )
        self._predictions[pid] = pred
        self._save()
        return pid

    def verify(
        self,
        prediction_id: str,
        correct: bool,
        notes: Optional[str] = None,
        verified_at: Optional[datetime] = None,
    ) -> Prediction:
        """Record the outcome of a prediction.

        Args:
            prediction_id: The ID returned by predict().
            correct: Whether the prediction was correct.
            notes: Optional notes about what this reveals.
            verified_at: When verification happened. Defaults to now.

        Returns:
            The updated Prediction.
        """
        if prediction_id not in self._predictions:
            raise KeyError(f"No prediction with id '{prediction_id}'")

        pred = self._predictions[prediction_id]
        pred.outcome = correct
        pred.verified_at = verified_at or datetime.now(timezone.utc)
        if notes is not None:
            pred.notes = notes
        self._save()
        return pred

    def add_completed(
        self,
        claim: str,
        confidence: float,
        domain: str,
        correct: bool,
        timestamp: Optional[datetime] = None,
        notes: Optional[str] = None,
        prediction_id: Optional[str] = None,
    ) -> str:
        """Add a prediction that already has an outcome.

        For batch importing historical data (e.g. from CALIBRATE.md).
        """
        confidence = _validate_confidence(confidence)
        pid = prediction_id or uuid.uuid4().hex[:8]
        now = timestamp or datetime.now(timezone.utc)

        pred = Prediction(
            id=pid,
            claim=claim,
            confidence=confidence,
            domain=domain,
            timestamp=now,
            outcome=correct,
            verified_at=now,
            notes=notes,
        )
        self._predictions[pid] = pred
        self._save()
        return pid

    def get(self, prediction_id: str) -> Prediction:
        """Get a prediction by ID."""
        if prediction_id not in self._predictions:
            raise KeyError(f"No prediction with id '{prediction_id}'")
        return self._predictions[prediction_id]

    @property
    def predictions(self) -> list[Prediction]:
        """All predictions, ordered by timestamp."""
        return sorted(self._predictions.values(), key=lambda p: p.timestamp)

    @property
    def verified(self) -> list[Prediction]:
        """Predictions that have been verified."""
        return [p for p in self.predictions if p.outcome is not None]

    @property
    def unverified(self) -> list[Prediction]:
        """Predictions still awaiting verification."""
        return [p for p in self.predictions if p.outcome is None]

    def generate_card(self) -> "TrustCard":
        """Generate a Trust Card from accumulated predictions.

        Requires at least 1 verified prediction.
        """
        from caliber.card import TrustCard

        return TrustCard.from_predictions(self.agent_name, self.verified)

    def _save(self) -> None:
        """Persist predictions to storage."""
        if self._storage is not None:
            self._storage.save(self.agent_name, list(self._predictions.values()))
