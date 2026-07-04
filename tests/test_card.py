"""Tests for caliber.card — Trust Card generation."""

import json
import pytest
from datetime import datetime, timezone

from caliber.tracker import TrustTracker, Prediction
from caliber.card import (
    TrustCard,
    BucketStats,
    DomainStats,
    BUCKET_RANGES,
    _exact_binomial_p_two_sided,
    _murphy_decomposition,
)
from caliber.storage import MemoryStorage


class TestBucketStats:
    def test_accuracy(self):
        b = BucketStats(label="70-79", predictions=10, correct=7)
        assert b.accuracy == 0.7

    def test_accuracy_empty(self):
        b = BucketStats(label="70-79", predictions=0, correct=0)
        assert b.accuracy is None

    def test_ci95_empty(self):
        b = BucketStats(label="70-79", predictions=0, correct=0)
        assert b.ci95 is None

    def test_expected_accuracy(self):
        b = BucketStats(label="70-79", predictions=1, correct=1)
        assert b.expected_accuracy == 0.745

    def test_expected_accuracy_uses_mean_confidence_when_available(self):
        b = BucketStats(
            label="70-79",
            predictions=10,
            correct=7,
            mean_confidence=0.70,
        )
        assert b.expected_accuracy == 0.70

    def test_calibration_gap_overconfident(self):
        # Expected ~74.5%, actual 50% → overconfident (positive gap)
        b = BucketStats(label="70-79", predictions=10, correct=5)
        assert b.calibration_gap > 0

    def test_calibration_gap_underconfident(self):
        # Expected ~74.5%, actual 90% → underconfident (negative gap)
        b = BucketStats(label="70-79", predictions=10, correct=9)
        assert b.calibration_gap < 0

    def test_to_dict(self):
        b = BucketStats(label="80-89", predictions=5, correct=4, mean_confidence=0.82)
        d = b.to_dict()
        assert d["predictions"] == 5
        assert d["correct"] == 4
        assert d["mean_confidence"] == 0.82
        assert d["accuracy"] == 0.8
        assert d["ci95"] == [0.376, 0.964]
        assert "calibration_gap" in d

    def test_wilson_interval_known_range(self):
        b = BucketStats(label="70-79", predictions=10, correct=5)
        lo, hi = b.ci95
        assert abs(lo - 0.237) < 0.001
        assert abs(hi - 0.763) < 0.001


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
        # Enough predictions in 60-69% bucket, all wrong -> danger zone.
        preds = self._make_predictions([(0.65, "a", False)] * 20)
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

    def test_danger_zone_requires_significance_not_untestable_gap(self):
        # D1 regression: 4 wrong predictions create a large gap, but
        # significance is None, so the bucket must not be flagged.
        preds = self._make_predictions([
            (0.65, "a", False),
            (0.62, "a", False),
            (0.68, "a", False),
            (0.64, "a", False),
        ])
        bucket = TrustCard.from_predictions("test", preds).confidence_buckets["60-69"]
        assert bucket.calibration_gap > 0.10
        assert bucket.significant is None
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
        assert "95% CI" in summary
        assert "Brier score" in summary
        assert "Calibration Z" in summary

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

    def test_card_level_proper_scores(self):
        preds = self._make_predictions([
            (0.80, "x", True),
            (0.80, "x", True),
            (0.80, "x", True),
            (0.80, "x", True),
            (0.80, "x", False),
        ])
        card = TrustCard.from_predictions("proper-score", preds)
        assert abs(card.brier_score - 0.16) < 1e-12
        assert abs(card.reliability) < 1e-12
        assert abs(card.resolution) < 1e-12
        assert abs(card.uncertainty - 0.16) < 1e-12
        assert abs(card.calibration_z) < 1e-12
        assert abs(card.calibration_p - 1.0) < 1e-12

        data = json.loads(card.to_json())
        cal = data["calibration"]
        assert cal["brier_score"] == 0.16
        assert cal["reliability"] == 0.0
        assert cal["resolution"] == 0.0
        assert cal["uncertainty"] == 0.16
        assert cal["calibration_z"] == 0.0
        assert cal["calibration_p"] == 1.0

    def test_murphy_identity(self):
        forecasts = [0.6, 0.7, 0.8, 0.9]
        outcomes = [0, 1, 1, 1]
        brier, reliability, resolution, uncertainty = _murphy_decomposition(
            forecasts,
            outcomes,
        )
        assert abs(brier - (reliability - resolution + uncertainty)) < 1e-12

    def test_bucket_gap_uses_mean_stated_confidence_not_midpoint(self):
        specs = [(0.70, "x", i < 7) for i in range(10)]
        preds = self._make_predictions(specs)
        card = TrustCard.from_predictions("mean-confidence", preds)
        bucket = card.confidence_buckets["70-79"]
        assert abs(bucket.mean_confidence - 0.70) < 1e-12
        assert bucket.accuracy == 0.70
        assert abs(bucket.calibration_gap) < 1e-12
        data = json.loads(card.to_json())
        assert data["calibration"]["confidence_buckets"]["70-79"]["mean_confidence"] == 0.7

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


class TestBucketSignificance:
    def test_insufficient_data(self):
        b = BucketStats(label="60-69", predictions=3, correct=1)
        assert b.significant is None  # too few for test

    def test_well_calibrated_not_significant(self):
        b = BucketStats(label="80-89", predictions=20, correct=17)
        assert b.significant is False  # 85% at 84.5% expected — no gap

    def test_large_miscalibration_significant(self):
        b = BucketStats(label="60-69", predictions=100, correct=50)
        assert b.significant is True  # 50% at 64.5% expected — real gap

    def test_significance_in_to_dict(self):
        b = BucketStats(label="70-79", predictions=10, correct=7)
        d = b.to_dict()
        assert "significant" in d
        assert isinstance(d["significant"], bool)

    def test_insufficient_in_to_dict(self):
        b = BucketStats(label="90-99", predictions=2, correct=2)
        d = b.to_dict()
        assert d.get("insufficient_data") is True

    def test_exact_binomial_known_value(self):
        p_value = _exact_binomial_p_two_sided(9, 10, 0.5)
        assert abs(p_value - 0.021484375) < 1e-9


class TestStrengthZones:
    def _make_predictions(self, specs):
        preds = []
        for i, (conf, domain, correct) in enumerate(specs):
            preds.append(Prediction(
                id=f"P-{i+1:03d}", claim=f"pred {i+1}",
                confidence=conf, domain=domain,
                timestamp=datetime(2026, 3, 24, tzinfo=timezone.utc),
                outcome=correct,
                verified_at=datetime(2026, 3, 24, tzinfo=timezone.utc),
            ))
        return preds

    def test_strength_zone_detected(self):
        # Enough predictions in 50-59%, all correct -> underconfident.
        preds = self._make_predictions([(0.55, "a", True)] * 20)
        card = TrustCard.from_predictions("test", preds)
        assert "50-59" in card.strength_zones

    def test_no_strength_zone_when_calibrated(self):
        preds = self._make_predictions([
            (0.85, "a", True),
            (0.82, "a", False),
            (0.88, "a", True),
        ])
        card = TrustCard.from_predictions("test", preds)
        assert card.strength_zones == []

    def test_strength_zone_in_json(self):
        preds = self._make_predictions([(0.55, "a", True)] * 20)
        card = TrustCard.from_predictions("test", preds)
        data = json.loads(card.to_json())
        assert "strength_zones" in data["calibration"]

    def test_strength_zone_requires_significance_not_untestable_gap(self):
        preds = self._make_predictions([
            (0.55, "a", True),
            (0.52, "a", True),
            (0.58, "a", True),
            (0.54, "a", True),
        ])
        bucket = TrustCard.from_predictions("test", preds).confidence_buckets["50-59"]
        assert bucket.calibration_gap < -0.10
        assert bucket.significant is None
        card = TrustCard.from_predictions("test", preds)
        assert "50-59" not in card.strength_zones
