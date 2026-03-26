"""Tests for caliber.tracker."""

import pytest
from datetime import datetime, timezone

from caliber.tracker import TrustTracker, Prediction, _validate_confidence
from caliber.storage import MemoryStorage


# --- Prediction ---

class TestPrediction:
    def test_roundtrip(self):
        p = Prediction(
            id="test-1",
            claim="sky is blue",
            confidence=0.90,
            domain="facts",
            timestamp=datetime(2026, 3, 24, tzinfo=timezone.utc),
            outcome=True,
            verified_at=datetime(2026, 3, 24, 0, 1, tzinfo=timezone.utc),
            notes="confirmed",
        )
        d = p.to_dict()
        p2 = Prediction.from_dict(d)
        assert p2.id == p.id
        assert p2.claim == p.claim
        assert p2.confidence == p.confidence
        assert p2.domain == p.domain
        assert p2.outcome == p.outcome
        assert p2.notes == p.notes

    def test_unverified_roundtrip(self):
        p = Prediction(
            id="test-2",
            claim="water is wet",
            confidence=0.70,
            domain="facts",
            timestamp=datetime(2026, 3, 24, tzinfo=timezone.utc),
        )
        d = p.to_dict()
        p2 = Prediction.from_dict(d)
        assert p2.outcome is None
        assert p2.verified_at is None


# --- Confidence validation ---

class TestValidateConfidence:
    def test_valid_range(self):
        assert _validate_confidence(0.50) == 0.50
        assert _validate_confidence(0.75) == 0.75
        assert _validate_confidence(0.99) == 0.99

    def test_int_coercion(self):
        # Int 0 is below range — should raise ValueError, not TypeError
        with pytest.raises(ValueError):
            _validate_confidence(0)

    def test_below_range(self):
        with pytest.raises(ValueError, match="0.50"):
            _validate_confidence(0.30)

    def test_above_range(self):
        with pytest.raises(ValueError, match="0.99"):
            _validate_confidence(1.0)

    def test_non_numeric(self):
        with pytest.raises(TypeError):
            _validate_confidence("high")


# --- TrustTracker ---

class TestTrustTracker:
    def _make_tracker(self, name="test-agent"):
        return TrustTracker(name, storage=MemoryStorage())

    def test_predict_returns_id(self):
        t = self._make_tracker()
        pid = t.predict("something", confidence=0.80, domain="test")
        assert isinstance(pid, str)
        assert len(pid) > 0

    def test_predict_with_explicit_id(self):
        t = self._make_tracker()
        pid = t.predict("something", confidence=0.80, domain="test", prediction_id="custom-1")
        assert pid == "custom-1"

    def test_verify(self):
        t = self._make_tracker()
        pid = t.predict("earth is round", confidence=0.95, domain="facts")
        result = t.verify(pid, correct=True, notes="confirmed")
        assert result.outcome is True
        assert result.notes == "confirmed"
        assert result.verified_at is not None

    def test_verify_nonexistent(self):
        t = self._make_tracker()
        with pytest.raises(KeyError):
            t.verify("ghost", correct=True)

    def test_predictions_ordered(self):
        t = self._make_tracker()
        t.predict("first", confidence=0.80, domain="a",
                  timestamp=datetime(2026, 1, 2, tzinfo=timezone.utc))
        t.predict("second", confidence=0.80, domain="a",
                  timestamp=datetime(2026, 1, 3, tzinfo=timezone.utc))
        t.predict("zeroth", confidence=0.80, domain="a",
                  timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
        preds = t.predictions
        assert preds[0].claim == "zeroth"
        assert preds[1].claim == "first"
        assert preds[2].claim == "second"

    def test_verified_vs_unverified(self):
        t = self._make_tracker()
        p1 = t.predict("a", confidence=0.80, domain="x")
        p2 = t.predict("b", confidence=0.80, domain="x")
        t.verify(p1, correct=True)
        assert len(t.verified) == 1
        assert len(t.unverified) == 1

    def test_add_completed(self):
        t = self._make_tracker()
        pid = t.add_completed(
            claim="known result",
            confidence=0.85,
            domain="test",
            correct=False,
            notes="historical import",
        )
        p = t.get(pid)
        assert p.outcome is False
        assert p.notes == "historical import"

    def test_generate_card(self):
        t = self._make_tracker()
        t.add_completed("a", 0.80, "x", True)
        t.add_completed("b", 0.70, "x", False)
        card = t.generate_card()
        assert card.agent_name == "test-agent"
        assert card.total_verified == 2
        assert card.overall_accuracy == 0.5

    def test_generate_card_empty(self):
        t = self._make_tracker()
        card = t.generate_card()
        assert card.total_verified == 0
        assert card.overall_accuracy is None

    def test_persistence(self):
        storage = MemoryStorage()
        t1 = TrustTracker("agent-a", storage=storage)
        pid = t1.predict("test", confidence=0.80, domain="x")
        t1.verify(pid, correct=True)

        # New tracker, same storage
        t2 = TrustTracker("agent-a", storage=storage)
        assert len(t2.predictions) == 1
        assert t2.predictions[0].outcome is True
