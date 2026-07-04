"""Property and coverage checks for Trust Card statistics."""

import math
import random

from hypothesis import given, settings, strategies as st

from caliber.card import (
    _exact_binomial_p_two_sided,
    _murphy_decomposition,
    _wilson_ci,
)


forecast_streams = st.lists(
    st.tuples(
        st.floats(
            min_value=0.001,
            max_value=0.999,
            allow_nan=False,
            allow_infinity=False,
        ),
        st.booleans(),
    ),
    min_size=1,
    max_size=80,
)


@given(forecast_streams)
@settings(deadline=None)
def test_murphy_identity_holds_for_random_streams(stream):
    forecasts = [forecast for forecast, _ in stream]
    outcomes = [1 if outcome else 0 for _, outcome in stream]

    brier, reliability, resolution, uncertainty = _murphy_decomposition(
        forecasts,
        outcomes,
    )

    assert abs(brier - (reliability - resolution + uncertainty)) < 1e-9


@given(
    st.integers(min_value=1, max_value=200).flatmap(
        lambda n: st.tuples(st.just(n), st.integers(min_value=0, max_value=n))
    )
)
def test_wilson_interval_bounds_and_contains_observed_rate(sample):
    n, correct = sample
    lo, hi = _wilson_ci(correct, n)
    observed = correct / n

    assert 0.0 <= lo <= hi <= 1.0
    assert lo <= observed <= hi


def _exact_wilson_coverage(n: int, p: float) -> float:
    covered = 0.0
    for correct in range(n + 1):
        lo, hi = _wilson_ci(correct, n)
        if lo <= p <= hi:
            covered += (
                math.comb(n, correct)
                * (p**correct)
                * ((1 - p) ** (n - correct))
            )
    return covered


def _monte_carlo_wilson_coverage(n: int, p: float, trials: int) -> float:
    rng = random.Random((n * 1000) + int(p * 1000) + trials)
    covered = 0
    for _ in range(trials):
        correct = sum(1 for _ in range(n) if rng.random() < p)
        lo, hi = _wilson_ci(correct, n)
        covered += lo <= p <= hi
    return covered / trials


def test_wilson_exact_coverage_grid_documents_discrete_small_n_behavior():
    """Wilson intervals are nominal 95%, but exact coverage is discrete.

    NORTHSTAR originally proposed accepting 93-97% Monte Carlo coverage for
    every cell in this grid. Exact enumeration shows that target is false for
    some small-n/extreme-p cells, so this test pins the real operating points
    instead of baking in a misleading pass condition.
    """

    expected_coverages = {
        (5, 0.55): 0.9312,
        (5, 0.70): 0.9692,
        (5, 0.85): 0.9734,
        (5, 0.95): 0.9774,
        (10, 0.55): 0.9494,
        (10, 0.70): 0.9244,
        (10, 0.85): 0.9500,
        (10, 0.95): 0.9139,
        (20, 0.55): 0.9597,
        (20, 0.70): 0.9752,
        (20, 0.85): 0.9781,
        (20, 0.95): 0.9245,
        (50, 0.55): 0.9545,
        (50, 0.70): 0.9567,
        (50, 0.85): 0.9558,
        (50, 0.95): 0.9622,
        (200, 0.55): 0.9453,
        (200, 0.70): 0.9466,
        (200, 0.85): 0.9410,
        (200, 0.95): 0.9672,
    }

    outside_original_band = []
    for (n, p), expected in expected_coverages.items():
        coverage = _exact_wilson_coverage(n, p)
        assert abs(coverage - expected) < 0.0001
        if not 0.93 <= coverage <= 0.97:
            outside_original_band.append((n, p, round(coverage, 4)))

    assert outside_original_band == [
        (5, 0.85, 0.9734),
        (5, 0.95, 0.9774),
        (10, 0.70, 0.9244),
        (10, 0.95, 0.9139),
        (20, 0.70, 0.9752),
        (20, 0.85, 0.9781),
        (20, 0.95, 0.9245),
    ]


def test_wilson_monte_carlo_tracks_exact_grid_coverage():
    trials = 2000
    for n in [5, 10, 20, 50, 200]:
        for p in [0.55, 0.70, 0.85, 0.95]:
            exact = _exact_wilson_coverage(n, p)
            simulated = _monte_carlo_wilson_coverage(n, p, trials)
            assert abs(simulated - exact) < 0.03


def test_exact_binomial_known_values():
    assert abs(_exact_binomial_p_two_sided(9, 10, 0.5) - 0.021484375) < 1e-9
    assert abs(_exact_binomial_p_two_sided(0, 5, 0.5) - 0.0625) < 1e-9
    assert abs(_exact_binomial_p_two_sided(5, 10, 0.5) - 1.0) < 1e-9


@given(
    st.integers(min_value=1, max_value=80).flatmap(
        lambda n: st.tuples(st.just(n), st.integers(min_value=0, max_value=n))
    )
)
def test_exact_binomial_half_null_is_symmetric(sample):
    n, correct = sample
    p_value = _exact_binomial_p_two_sided(correct, n, 0.5)
    mirrored = _exact_binomial_p_two_sided(n - correct, n, 0.5)

    assert 0.0 <= p_value <= 1.0
    assert abs(p_value - mirrored) < 1e-12
