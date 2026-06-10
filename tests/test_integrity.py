"""Tests for caliber.integrity — gaming-signature detection."""

from datetime import datetime, timedelta, timezone

from caliber.tracker import Prediction
from caliber.integrity import (
    IntegrityReport,
    _murphy_decomposition,
    MIN_N_BEHAVIORAL,
    MIN_N_DISTRIBUTIONAL,
)


T0 = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def make_pred(
    i,
    confidence,
    outcome,
    domain="codebase",
    claim=None,
    predicted_at=None,
    verify_after=timedelta(hours=1),
):
    ts = predicted_at or (T0 + timedelta(minutes=i))
    return Prediction(
        id=f"p{i:04d}",
        claim=claim if claim is not None else f"distinct claim number {i}",
        confidence=confidence,
        domain=domain,
        timestamp=ts,
        outcome=outcome,
        verified_at=ts + verify_after,
    )


def honest_predictions():
    """24 predictions: spread confidence, mixed outcomes, 3 domains."""
    preds = []
    domains = ["codebase", "behavior", "architecture"]
    i = 0
    for conf, n, n_correct in [(0.55, 8, 4), (0.75, 8, 6), (0.95, 8, 8)]:
        for j in range(n):
            preds.append(
                make_pred(
                    i,
                    conf,
                    outcome=j < n_correct,
                    domain=domains[i % 3],
                )
            )
            i += 1
    return preds


def farmer_predictions(n=30):
    """All 0.95, all correct, one domain, repeated claims, instant verify."""
    return [
        make_pred(
            i,
            0.95,
            outcome=True,
            domain="filesystem",
            claim=f"file number {i % 10} exists",
            verify_after=timedelta(seconds=5),
        )
        for i in range(n)
    ]


class TestMurphyDecomposition:
    def test_hand_computed(self):
        # f=0.8 o=1 -> 0.04 ; f=0.6 o=0 -> 0.36 ; brier = 0.20
        brier, rel, res, unc = _murphy_decomposition([0.8, 0.6], [1, 0])
        assert abs(brier - 0.20) < 1e-12
        assert abs(rel - 0.20) < 1e-12
        assert abs(res - 0.25) < 1e-12
        assert abs(unc - 0.25) < 1e-12

    def test_identity_holds(self):
        forecasts = [0.55, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.95, 0.6]
        outcomes = [0, 1, 1, 0, 1, 1, 1, 1, 0, 1]
        brier, rel, res, unc = _murphy_decomposition(forecasts, outcomes)
        assert abs(brier - (rel - res + unc)) < 1e-9

    def test_perfect_farmer_components(self):
        brier, rel, res, unc = _murphy_decomposition([0.95] * 20, [1] * 20)
        assert unc == 0.0  # no outcome variance
        assert res == 0.0  # nothing to discriminate
        assert abs(brier - 0.0025) < 1e-12


class TestFarmerDetection:
    def test_farmer_raises_flags(self):
        report = IntegrityReport.from_predictions(
            "farmer", farmer_predictions()
        )
        codes = {f.code for f in report.flags}
        assert "LOW_OUTCOME_VARIANCE" in codes
        assert "CONFIDENCE_CONCENTRATION" in codes
        assert "DOMAIN_CONCENTRATION" in codes
        assert "DUPLICATE_CLAIMS" in codes
        assert "INSTANT_VERIFICATION" in codes
        assert "gaming signature" in report.verdict

    def test_farmer_metrics(self):
        report = IntegrityReport.from_predictions(
            "farmer", farmer_predictions()
        )
        assert report.outcome_base_rate == 1.0
        assert report.uncertainty == 0.0
        assert report.top_bucket_share == 1.0
        assert report.domain_hhi == 1.0
        assert report.duplicate_claim_ratio > 0.6
        assert report.instant_verify_share == 1.0
        assert report.median_verify_latency_seconds == 5.0

    def test_no_discrimination_not_doubled(self):
        # When uncertainty is already near zero, NO_DISCRIMINATION would be
        # redundant with LOW_OUTCOME_VARIANCE and must not also fire.
        report = IntegrityReport.from_predictions(
            "farmer", farmer_predictions()
        )
        codes = {f.code for f in report.flags}
        assert "NO_DISCRIMINATION" not in codes


class TestHonestAgent:
    def test_no_flags(self):
        report = IntegrityReport.from_predictions(
            "honest", honest_predictions()
        )
        assert report.flags == []
        assert "No gaming signatures" in report.verdict

    def test_metrics_reasonable(self):
        report = IntegrityReport.from_predictions(
            "honest", honest_predictions()
        )
        assert abs(report.outcome_base_rate - 0.75) < 1e-9
        assert abs(report.uncertainty - 0.1875) < 1e-9
        assert report.resolution > 0.0
        assert report.import_share == 0.0
        assert report.instant_verify_share == 0.0


class TestNoDiscrimination:
    def test_flat_confidence_varied_outcomes(self):
        # Outcomes vary (base rate 0.5) but confidence never moves:
        # stated confidence carries no information.
        preds = [
            make_pred(i, 0.75, outcome=(i % 2 == 0)) for i in range(20)
        ]
        report = IntegrityReport.from_predictions("flat", preds)
        codes = {f.code for f in report.flags}
        assert "NO_DISCRIMINATION" in codes
        assert "LOW_OUTCOME_VARIANCE" not in codes


class TestImportedHistory:
    def test_batch_import_flagged(self):
        # timestamp == verified_at is the add_completed / import signature
        preds = [
            Prediction(
                id=f"i{i}",
                claim=f"imported claim {i}",
                confidence=0.7 + (i % 3) * 0.1,
                domain=["a", "b", "c"][i % 3],
                timestamp=T0 + timedelta(minutes=i),
                outcome=(i % 4 != 0),
                verified_at=T0 + timedelta(minutes=i),
            )
            for i in range(12)
        ]
        report = IntegrityReport.from_predictions("imported", preds)
        assert report.import_share == 1.0
        # No live verifications -> no latency stats
        assert report.instant_verify_share is None
        assert report.median_verify_latency_seconds is None
        codes = {f.code for f in report.flags}
        assert "UNWITNESSED_HISTORY" in codes
        assert "INSTANT_VERIFICATION" not in codes


class TestSampleSizeGates:
    def test_below_behavioral_gate_no_flags(self):
        preds = farmer_predictions(MIN_N_BEHAVIORAL - 1)
        report = IntegrityReport.from_predictions("tiny", preds)
        assert report.flags == []
        assert report.insufficient_data
        assert "Insufficient data" in report.verdict

    def test_between_gates_only_behavioral_flags(self):
        preds = farmer_predictions(MIN_N_DISTRIBUTIONAL - 1)
        report = IntegrityReport.from_predictions("mid", preds)
        codes = {f.code for f in report.flags}
        assert "DUPLICATE_CLAIMS" in codes
        assert "INSTANT_VERIFICATION" in codes
        assert "CONFIDENCE_CONCENTRATION" not in codes
        assert "LOW_OUTCOME_VARIANCE" not in codes
        assert "DOMAIN_CONCENTRATION" not in codes

    def test_empty(self):
        report = IntegrityReport.from_predictions("empty", [])
        assert report.n_verified == 0
        assert report.flags == []
        assert "nothing to analyze" in report.verdict

    def test_unverified_excluded(self):
        preds = farmer_predictions(30)
        for p in preds[:25]:
            p.outcome = None
        report = IntegrityReport.from_predictions("partial", preds)
        assert report.n_verified == 5
        assert report.insufficient_data


class TestDuplicateNormalization:
    def test_case_and_whitespace_variants_count(self):
        claims = ["The file EXISTS", "the file exists", "  the   file exists "]
        preds = [
            make_pred(i, 0.6 + 0.1 * (i % 4), outcome=(i % 3 != 0),
                      claim=claims[i % 3], domain=["a", "b"][i % 2])
            for i in range(12)
        ]
        report = IntegrityReport.from_predictions("dup", preds)
        # 12 claims normalize to 1 unique -> ratio 11/12
        assert report.duplicate_claim_ratio > 0.9
        codes = {f.code for f in report.flags}
        assert "DUPLICATE_CLAIMS" in codes


class TestSerialization:
    def test_to_dict_shape(self):
        report = IntegrityReport.from_predictions(
            "farmer", farmer_predictions()
        )
        d = report.to_dict()
        assert d["agent_name"] == "farmer"
        assert d["n_verified"] == 30
        assert "verdict" in d
        assert d["metrics"]["uncertainty"] == 0.0
        assert d["metrics"]["brier_score"] == 0.0025
        flag_codes = [f["code"] for f in d["flags"]]
        assert "LOW_OUTCOME_VARIANCE" in flag_codes
        for f in d["flags"]:
            assert f["evidence"]  # every flag carries evidence

    def test_summary_readable(self):
        report = IntegrityReport.from_predictions(
            "farmer", farmer_predictions()
        )
        text = report.summary()
        assert "Integrity Report: farmer" in text
        assert "Brier score" in text
        assert "LOW_OUTCOME_VARIANCE" in text
        assert "evidence:" in text

    def test_honest_summary_clean(self):
        report = IntegrityReport.from_predictions(
            "honest", honest_predictions()
        )
        text = report.summary()
        assert "No gaming signatures" in text
        assert "⚠" not in text
