"""Fast regression tests for the Phase 2 adversarial benchmark."""

import pytest

from lab import run_bench


FAST_REPLICATES = 50
NORTHSTAR_N = 100


@pytest.fixture(scope="module")
def bench_rows():
    result = run_bench.run_bench(
        replicates=FAST_REPLICATES,
        sample_sizes=(NORTHSTAR_N,),
        sha="testsha",
    )
    return {row["population"]: row for row in result["rows"]}


def test_clean_and_boundary_populations_stay_under_flag_budget(bench_rows):
    for population in (
        "honest",
        "overconfident",
        "underconfident",
        "noisy",
        "smart_fabricator",
    ):
        assert bench_rows[population]["any_flag_rate"] <= 0.05


def test_attack_populations_trip_expected_flags_with_high_power(bench_rows):
    expected_flags = {
        "farmer": (
            "LOW_OUTCOME_VARIANCE",
            "CONFIDENCE_CONCENTRATION",
            "DOMAIN_CONCENTRATION",
            "INSTANT_VERIFICATION",
        ),
        "patient_farmer": (
            "LOW_OUTCOME_VARIANCE",
            "CONFIDENCE_CONCENTRATION",
            "DOMAIN_CONCENTRATION",
        ),
        "naive_fabricator": (
            "NO_DISCRIMINATION",
            "SUSPICIOUSLY_PERFECT",
        ),
        "template_spammer": ("NO_DISCRIMINATION",),
        "duplicate_spammer": ("DUPLICATE_CLAIMS",),
        "domain_camper": ("DOMAIN_CONCENTRATION",),
        "bulk_importer": ("UNWITNESSED_HISTORY",),
    }

    for population, flags in expected_flags.items():
        assert bench_rows[population]["any_flag_rate"] >= 0.95
        for flag in flags:
            assert bench_rows[population]["flag_rates"][flag] >= 0.95


def test_patient_farmer_is_caught_without_latency_flag(bench_rows):
    assert bench_rows["patient_farmer"]["any_flag_rate"] >= 0.95
    assert bench_rows["patient_farmer"]["flag_rates"]["INSTANT_VERIFICATION"] <= 0.05
