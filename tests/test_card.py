"""Tests for caliber.card — Trust Card generation."""

import json
import pytest
from datetime import datetime, timezone

from caliber.tracker import TrustTracker, Prediction
from caliber.card import TrustCard, BucketStats, DomainStats, BUCKET_RANGES
from caliber.storage import MemoryStorage


class TestBucketStats:
    def test_accuracy(self):
        b = BucketStats(label="70-79", predictions=10, correct=7)
        assert b.accuracy == 0.7

    def test_accuracy_empty(self):
        b = BucketStats(label="70-79", predictions=0, correct=0)
        assert b.accuracy is None

    def test_expected_accuracy(self):
        b = BucketStats(label="70-79", predictions=1, correct=1)
        assert b.expected_accuracy == 0.745

    def test_calibration_gap_overconfident(self):
        # Expected ~74.5%, actual 50% → overconfident (positive gap)
        b = BucketStats(label="70-79", predictions=10, correct=5)
        assert b.calibration_gap > 0

    def test_calibration_gap_underconfident(self):
        # Expected ~74.5%, actual 90% → underconfident (negative gap)
        b = BucketStats(label="70-79", predictions=10, correct=9)
        assert b.calibration_gap < 0

    def test_to_dict(self):
        b = BucketStats(label="80-89", predictions=5, correct=4)
        d = b.to_dict()
        assert d["predictions"] == 5
        assert d["correct"] == 4
        assert d["accuracy"] == 0.8
        assert "calibration_gap" in d


class TestDomainStats:
    def test_accuracy(self):
        d = DomainStats(domain="codebase", predictions=6, correct=5, avg_confidence=0.73)
        assert abs(d.accuracy - 0.833) < 0.01

    def test_to_dict(self):
        d = DomainStats(domain="test", predictions=3, correct=2, avg_confidence=0.75)
        out = d.to_dict()
        assert out["predictions"] == 3
        assert out["avg_confidence"] == 0.75


class TestTrustCard:
    def _make_predictions(self, specs: list[tuple]) -> list[Prediction]:
        """Make predictions from (confidence, domain, correct) tuples."""
        preds = []
        for i, (conf, domain, correct) in enumerate(specs):
            preds.append(Prediction(
                id=f"P-{i+1:03d}",
                claim=f"prediction {i+1}",
                confidence=conf,
                domain=domain,
                timestamp=datetime(2026, 3, 24, tzinfo=timezone.utc),
                outcome=correct,
                verified_at=datetime(2026, 3, 24, 0, 1, tzinfo=timezone.utc),
            ))
        return preds

    def test_from_empty(self):
        card = TrustCard.from_predictions("empty-agent", [])
        assert card.total_verified == 0
        assert card.overall_accuracy is None
        assert card.danger_zones == []

    def test_basic_stats(self):
        preds = self._make_predictions([
            (0.80, "x", True),
            (0.80, "x", True),
            (0.80, "x", False),
        ])
        card = TrustCard.from_predictions("test", preds)
        assert card.total_verified == 3
        assert abs(card.overall_accuracy - 0.667) < 0.01
        assert abs(card.mean_confidence - 0.80) < 0.01

    def test_confidence_buckets(self):
        preds = self._make_predictions([
            (0.55, "a", True),   # 50-59
            (0.65, "a", False),  # 60-69
            (0.75, "a", True),   # 70-79
            (0.85, "a", True),   # 80-89
            (0.95, "a", True),   # 90-99
        ])
        card = TrustCard.from_predictions("test", preds)
        assert card.confidence_buckets["50-59"].predictions == 1
        assert card.confidence_buckets["60-69"].predictions == 1
        assert card.confidence_buckets["90-99"].accuracy == 1.0

    def test_domain_breakdown(self):
        preds = self._make_predictions([
            (0.80, "security", True),
            (0.80, "security", False),
            (0.80, "style", True),
        ])
        card = TrustCard.from_predictions("test", preds)
        assert "security" in card.domains
        assert "style" in card.domains
        assert card.domains["security"].predictions == 2
        assert card.domains["style"].accuracy == 1.0

    def test_danger_zone_detection(self):
        # 3+ predictions in 60-69% bucket, all wrong → danger zone
        preds = self._make_predictions([
            (0.65, "a", False),
            (0.62, "a", False),
            (0.68, "a", False),
        ])
        card = TrustCard.from_predictions("test", preds)
        assert "60-69" in card.danger_zones

    def test_no_danger_zone_when_accurate(self):
        preds = self._make_predictions([
            (0.65, "a", True),
            (0.62, "a", True),
            (0.68, "a", True),
        ])
        card = TrustCard.from_predictions("test", preds)
        assert card.danger_zones == []

    def test_danger_zone_needs_min_sample(self):
        # Only 2 predictions — not enough to flag as danger zone
        preds = self._make_predictions([
            (0.65, "a", False),
            (0.62, "a", False),
        ])
        card = TrustCard.from_predictions("test", preds)
        assert "60-69" not in card.danger_zones

    def test_to_json_roundtrip(self):
        preds = self._make_predictions([
            (0.80, "x", True),
            (0.65, "y", False),
        ])
        card = TrustCard.from_predictions("test", preds)
        j = card.to_json()
        data = json.loads(j)
        assert data["agent_name"] == "test"
        assert data["trust_version"] == "0.1"
        assert "calibration" in data

    def test_summary_output(self):
        preds = self._make_predictions([
            (0.80, "code", True),
            (0.70, "code", False),
            (0.90, "facts", True),
        ])
        card = TrustCard.from_predictions("test", preds)
        summary = card.summary()
        assert "test" in summary
        assert "Overall accuracy" in summary
        assert "code" in summary

    def test_perfect_calibration(self):
        """Agent that's right exactly as often as confidence implies."""
        preds = self._make_predictions([
            (0.80, "x", True),
            (0.80, "x", True),
            (0.80, "x", True),
            (0.80, "x", True),
            (0.80, "x", False),  # 4/5 = 80% accuracy at 80% confidence
        ])
        card = TrustCard.from_predictions("perfect", preds)
        bucket = card.confidence_buckets["80-89"]
        assert abs(bucket.calibration_gap) < 0.06  # close to 0

    def test_real_data_volume(self):
        """Simulate MY UNIVERSE scale — 36 predictions."""
        import random
        random.seed(42)
        preds = []
        for i in range(36):
            conf = random.choice([0.55, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90])
            correct = random.random() < conf  # probabilistically correct
            preds.append(Prediction(
                id=f"P-{i+1:03d}",
                claim=f"pred {i+1}",
                confidence=conf,
                domain=random.choice(["a", "b", "c"]),
                timestamp=datetime(2026, 3, 24, tzinfo=timezone.utc),
                outcome=correct,
                verified_at=datetime(2026, 3, 24, tzinfo=timezone.utc),
            ))
        card = TrustCard.from_predictions("volume-test", preds)
        assert card.total_verified == 36
        assert 0 < card.overall_accuracy < 1
        assert len(card.domains) <= 3
