"""Tests for the Phase 2 adversarial-lab simulators."""

from caliber.integrity import IntegrityReport
from lab import simulate


def _codes(records):
    report = IntegrityReport.from_predictions("sim", simulate.to_predictions(records))
    return {flag.code for flag in report.flags}, report


def test_population_registry_has_required_northstar_generators():
    assert set(simulate.POPULATIONS) == {
        "honest",
        "overconfident",
        "underconfident",
        "noisy",
        "farmer",
        "patient_farmer",
        "naive_fabricator",
        "smart_fabricator",
        "template_spammer",
        "domain_camper",
        "bulk_importer",
    }


def test_simulators_are_deterministic_and_prediction_compatible():
    first = simulate.honest(25, 7)
    second = simulate.honest(25, 7)

    assert first == second
    predictions = simulate.to_predictions(first)
    assert len(predictions) == 25
    assert predictions[0].id == first[0]["id"]
    assert predictions[0].timestamp == first[0]["timestamp"]


def test_farmer_trips_current_farming_flags():
    codes, report = _codes(simulate.farmer(120, 1, easy_share=0.9))

    assert "LOW_OUTCOME_VARIANCE" in codes
    assert "CONFIDENCE_CONCENTRATION" in codes
    assert "DOMAIN_CONCENTRATION" in codes
    assert "INSTANT_VERIFICATION" in codes
    assert report.template_claim_ratio > 0.8


def test_patient_farmer_beats_latency_but_not_distributional_flags():
    codes, _report = _codes(simulate.patient_farmer(120, 1, easy_share=0.9))

    assert "INSTANT_VERIFICATION" not in codes
    assert "LOW_OUTCOME_VARIANCE" in codes
    assert "CONFIDENCE_CONCENTRATION" in codes


def test_naive_fabricator_trips_mendel_flag():
    codes, report = _codes(simulate.naive_fabricator(120, 3))

    assert "SUSPICIOUSLY_PERFECT" in codes
    assert report.mendel_p_low < 0.01


def test_smart_fabricator_is_a_record_only_boundary_case():
    codes, report = _codes(simulate.smart_fabricator(200, 11))

    assert codes == set()
    assert 0.10 < report.uncertainty < 0.25


def test_domain_camper_targets_domain_concentration():
    codes, report = _codes(simulate.domain_camper(80, 4, k_domains=1))

    assert "DOMAIN_CONCENTRATION" in codes
    assert report.domain_hhi == 1.0


def test_bulk_importer_targets_unwitnessed_history():
    codes, report = _codes(simulate.bulk_importer(80, 5, import_share=0.85))

    assert "UNWITNESSED_HISTORY" in codes
    assert report.import_share == 0.85


def test_mixture_combines_honest_and_attacker_streams():
    records = simulate.mixture(
        100,
        9,
        honest_frac=0.4,
        attacker=simulate.farmer,
        easy_share=1.0,
    )
    codes, _report = _codes(records)

    assert len(records) == 100
    assert len({record["id"] for record in records}) == 100
    assert "CONFIDENCE_CONCENTRATION" in codes
