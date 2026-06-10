"""Red-team tests for caliber.integrity — gaming strategies as test cases.

Each test encodes an evasion strategy an adversary could use against the
integrity flags. Tests assert either that the strategy is caught, or — for
known residual limitations — document exactly what currently slips through
so a future fix flips the assertion deliberately rather than silently.
"""

from datetime import datetime, timedelta, timezone

from caliber.tracker import Prediction
from caliber.integrity import (
    IntegrityReport,
    _chi2_cdf,
    _mendel_test,
)


T0 = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def make_pred(i, confidence, outcome, domain, claim, verify_after_hours=4.0):
    ts = T0 + timedelta(minutes=7 * i)
    return Prediction(
        id=f"a{i:04d}",
        claim=claim,
        confidence=confidence,
        domain=domain,
        timestamp=ts,
        outcome=outcome,
        verified_at=ts + timedelta(hours=verify_after_hours),
    )


def calibrated_forger_predictions():
    """Strategy A: fabricate outcomes that exactly match stated confidence.

    Distinct claims, three domains, slow verification, spread confidence —
    every behavioral signal looks clean. Outcomes are invented so each
    bucket's accuracy equals its mean confidence exactly.
    """
    preds = []
    domains = ["api", "codebase", "behavior"]
    i = 0
    # (confidence, n, fabricated correct count = confidence * n exactly)
    for conf, n in [(0.60, 20), (0.75, 20), (0.90, 20)]:
        correct_count = round(conf * n)
        for j in range(n):
            preds.append(
                make_pred(
                    i,
                    conf,
                    outcome=j < correct_count,
                    domain=domains[i % 3],
                    claim=f"the {domains[i % 3]} module property {i} holds",
                )
            )
            i += 1
    return preds


def honest_noisy_predictions():
    """Honest agent: same shape as the forger but outcomes scatter around
    confidence the way real binomial outcomes do (~1 SE deviations)."""
    preds = []
    domains = ["api", "codebase", "behavior"]
    i = 0
    # Deviations of roughly one binomial SE from expectation per bucket
    for conf, n, correct_count in [(0.60, 20, 14), (0.75, 20, 13), (0.90, 20, 17)]:
        for j in range(n):
            preds.append(
                make_pred(
                    i,
                    conf,
                    outcome=j < correct_count,
                    domain=domains[i % 3],
                    claim=f"distinct honest claim number {i}",
                )
            )
            i += 1
    return preds


class TestChi2Approximation:
    def test_cdf_monotone_and_bounded(self):
        last = 0.0
        for x in (0.1, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0):
            v = _chi2_cdf(x, 3)
            assert 0.0 <= v <= 1.0
            assert v >= last
            last = v

    def test_cdf_median_near_known_value(self):
        # Chi-square(3) median is ~2.366; CDF there should be ~0.5
        assert abs(_chi2_cdf(2.366, 3) - 0.5) < 0.02

    def test_cdf_zero(self):
        assert _chi2_cdf(0.0, 3) == 0.0


class TestCalibratedForger:
    """Strategy A: outcome fabrication matched to confidence."""

    def test_evades_all_behavioral_flags(self):
        # The forger's record is clean on every behavioral signal —
        # this documents WHY the Mendel test is needed.
        report = IntegrityReport.from_predictions(
            "forger", calibrated_forger_predictions()
        )
        codes = {f.code for f in report.flags}
        assert "LOW_OUTCOME_VARIANCE" not in codes
        assert "CONFIDENCE_CONCENTRATION" not in codes
        assert "DOMAIN_CONCENTRATION" not in codes
        assert "DUPLICATE_CLAIMS" not in codes
        assert "INSTANT_VERIFICATION" not in codes
        assert "UNWITNESSED_HISTORY" not in codes

    def test_caught_by_mendel(self):
        report = IntegrityReport.from_predictions(
            "forger", calibrated_forger_predictions()
        )
        codes = {f.code for f in report.flags}
        assert "SUSPICIOUSLY_PERFECT" in codes
        assert report.mendel_p_low < 0.01

    def test_honest_noise_not_flagged(self):
        report = IntegrityReport.from_predictions(
            "honest", honest_noisy_predictions()
        )
        codes = {f.code for f in report.flags}
        assert "SUSPICIOUSLY_PERFECT" not in codes
        # Honest scatter sits comfortably inside the chi-square body
        assert report.mendel_p_low > 0.05

    def test_mendel_needs_bucket_spread(self):
        # Two buckets only -> no test, no flag, no false certainty
        forecasts = [0.75] * 20 + [0.95] * 20
        outcomes = [1] * 15 + [0] * 5 + [1] * 19 + [0]
        assert _mendel_test(forecasts, outcomes) is None


class TestKnownResidualLimitations:
    """Strategies that still evade detection — documented, not hidden."""

    def test_templated_claims_measured_not_flagged(self):
        # Strategy C: template farming. "file N exists" with a varying N
        # defeats the exact-match duplicate detector. The template ratio
        # metric exposes it, but deliberately does NOT flag: honest bulk
        # workloads are equally templated. The farming itself is still
        # caught by LOW_OUTCOME_VARIANCE.
        preds = [
            make_pred(
                i, 0.95, outcome=True, domain="filesystem",
                claim=f"file number {i} exists on disk",
            )
            for i in range(25)
        ]
        report = IntegrityReport.from_predictions("templater", preds)
        codes = {f.code for f in report.flags}
        assert report.duplicate_claim_ratio == 0.0  # exact-match gap remains
        assert report.template_claim_ratio > 0.9  # but templating is visible
        assert "LOW_OUTCOME_VARIANCE" in codes  # farming still caught

    def test_honest_bulk_user_not_punished_for_templates(self):
        # The reason template ratio is a metric, not a flag: an honest
        # agent scanning 30 packages produces templated claims with real
        # outcome variance and honest calibration. No flag may fire.
        # Confidence must actually discriminate outcomes (else
        # NO_DISCRIMINATION fires, correctly): 5/10 at 55%, 8/10 at 75%,
        # 10/10 at 92% — calibrated with honest scatter.
        preds = []
        i = 0
        for conf, correct_count in [(0.55, 5), (0.75, 8), (0.92, 10)]:
            for j in range(10):
                preds.append(
                    make_pred(
                        i, conf, outcome=j < correct_count,
                        domain=["pypi", "github", "security"][i % 3],
                        claim=f"package number {i} is maintained upstream",
                        verify_after_hours=2.0,
                    )
                )
                i += 1
        report = IntegrityReport.from_predictions("bulk-scanner", preds)
        assert report.template_claim_ratio > 0.9  # fully templated
        assert report.flags == []  # and entirely unflagged

    def test_patient_farmer_evades_latency_check(self):
        # Strategy D: wait out the instant-verification window. Any fixed
        # window can be beaten by a timer; latency alone is advisory.
        preds = [
            make_pred(
                i, 0.95, outcome=True, domain="filesystem",
                claim=f"trivial but patient claim {i}",
                verify_after_hours=0.05,  # 3 minutes > 120s window
            )
            for i in range(25)
        ]
        report = IntegrityReport.from_predictions("patient", preds)
        codes = {f.code for f in report.flags}
        assert "INSTANT_VERIFICATION" not in codes  # the gap
        assert "LOW_OUTCOME_VARIANCE" in codes  # still caught

    def test_synthetic_import_timestamps_evade_import_share(self):
        # Strategy E: an importer that invents a verified_at offset defeats
        # the timestamp-equality import heuristic. Only the commitment
        # scheme (signed=True) can prove witnessed timing.
        preds = [
            make_pred(
                i, 0.6 + (i % 4) * 0.1, outcome=(i % 4 != 0),
                domain=["a", "b", "c"][i % 3],
                claim=f"backfilled claim {i}",
                verify_after_hours=float(1 + i % 5),
            )
            for i in range(24)
        ]
        report = IntegrityReport.from_predictions("backfiller", preds)
        assert report.import_share == 0.0  # the gap
        codes = {f.code for f in report.flags}
        assert "UNWITNESSED_HISTORY" not in codes  # the gap


class TestMendelSerialization:
    def test_metrics_include_mendel(self):
        report = IntegrityReport.from_predictions(
            "forger", calibrated_forger_predictions()
        )
        d = report.to_dict()
        assert "mendel_p_low" in d["metrics"]
        assert d["metrics"]["mendel_buckets"] == 3
        flag = next(
            f for f in d["flags"] if f["code"] == "SUSPICIOUSLY_PERFECT"
        )
        assert flag["evidence"]["p_low"] < 0.01
