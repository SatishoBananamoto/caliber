# Caliber Northstar Lab Notebook

This notebook is the working evidence trail for the `northstar` branch. It is
not shipped in the package.

## BASELINE

Date: 2026-07-04
Branch: `northstar`
Base commit: `ab54e5b`

### Repository State

Phase 0 directive source: `NORTHSTAR.md`

Required read pass completed:

- `GAUGE.md`
- `REVIEW.md`
- `caliber/__init__.py`
- `caliber/card.py`
- `caliber/cli.py`
- `caliber/commitment.py`
- `caliber/importer.py`
- `caliber/integrity.py`
- `caliber/mcp_server.py`
- `caliber/storage.py`
- `caliber/tracker.py`
- `caliber/trajectory.py`
- `tests/test_integrity_adversarial.py`

Merged branch cleanup:

```text
$ git branch -d integrity-metrics
Deleted branch integrity-metrics (was e485eba).
```

Working branch:

```text
$ git checkout -b northstar
Switched to a new branch 'northstar'
```

### Baseline Tests

```text
$ python3 -m pytest -q
........................................................................ [ 50%]
.......................................................................  [100%]
143 passed in 4.23s
```

### Local Corpora Inventory

Observed store files:

```text
/home/satishocoin/.caliber/test.json
/home/satishocoin/.caliber/default.json
/home/satishocoin/.caliber/claude-trader.json
```

Observed summaries:

```text
$ python3 -m caliber.cli -a default summary
Agent: default
Total predictions: 20
  Verified: 20
  Unverified: 0
  Accuracy: 90.0% (18/20)
  Avg confidence: 77.5%
  Calibration: underconfident by 12%
  Strongest: architecture (4/4)
  Weakest: codebase (6/8)

  Need ~80 more per bucket for statistical significance.
```

```text
$ python3 -m caliber.cli -a test summary
Agent: test
Total predictions: 88
  Verified: 88
  Unverified: 0
  Accuracy: 77.3% (68/88)
  Avg confidence: 70.7%
  Calibration: underconfident by 7%
  Strongest: tooling (4/4)
  Weakest: behavior (20/30)

  Need ~12 more per bucket for statistical significance.
```

```text
$ python3 -m caliber.cli -a claude-trader summary
Agent: claude-trader
Total predictions: 5
  Verified: 0
  Unverified: 5
```

`NORTHSTAR.md` says the imported CALIBRATE corpus is approximately 94 verified
predictions. Current local evidence shows `test` has 88 verified predictions.
The notebook treats 88 as authoritative for this checkout.

### Baseline Card: default

```json
{
  "trust_version": "0.1",
  "agent_name": "default",
  "generated": "2026-07-04T01:09:33.297210+00:00",
  "calibration": {
    "total_predictions": 20,
    "total_verified": 20,
    "overall_accuracy": 0.9,
    "mean_confidence": 0.775,
    "mean_calibration_gap": -0.105,
    "confidence_buckets": {
      "50-59": {
        "predictions": 1,
        "correct": 0,
        "accuracy": 0.0,
        "calibration_gap": 0.545,
        "insufficient_data": true
      },
      "60-69": {
        "predictions": 2,
        "correct": 2,
        "accuracy": 1.0,
        "calibration_gap": -0.355,
        "insufficient_data": true
      },
      "70-79": {
        "predictions": 6,
        "correct": 6,
        "accuracy": 1.0,
        "calibration_gap": -0.255,
        "significant": false
      },
      "80-89": {
        "predictions": 8,
        "correct": 7,
        "accuracy": 0.875,
        "calibration_gap": -0.03,
        "significant": false
      },
      "90-99": {
        "predictions": 3,
        "correct": 3,
        "accuracy": 1.0,
        "calibration_gap": -0.055,
        "insufficient_data": true
      }
    },
    "domains": {
      "architecture": {
        "predictions": 4,
        "correct": 4,
        "avg_confidence": 0.775,
        "accuracy": 1.0
      },
      "behavior": {
        "predictions": 5,
        "correct": 5,
        "avg_confidence": 0.7,
        "accuracy": 1.0
      },
      "codebase": {
        "predictions": 8,
        "correct": 6,
        "avg_confidence": 0.812,
        "accuracy": 0.75
      },
      "security": {
        "predictions": 3,
        "correct": 3,
        "avg_confidence": 0.8,
        "accuracy": 1.0
      }
    }
  }
}
```

### Baseline Integrity: default

```json
{
  "agent_name": "default",
  "generated": "2026-07-04T01:09:33.063352+00:00",
  "n_verified": 20,
  "verdict": "2 gaming signature(s) detected in 20 verified predictions.",
  "metrics": {
    "brier_score": 0.0998,
    "reliability": 0.0622,
    "resolution": 0.0525,
    "uncertainty": 0.09,
    "outcome_base_rate": 0.9,
    "top_bucket_share": 0.15,
    "confidence_entropy": 0.8651,
    "domain_hhi": 0.285,
    "duplicate_claim_ratio": 0.0,
    "template_claim_ratio": 0.0,
    "import_share": 0.0,
    "instant_verify_share": 0.7,
    "median_verify_latency_seconds": 53.5326
  },
  "flags": [
    {
      "code": "LOW_OUTCOME_VARIANCE",
      "message": "Outcomes are nearly uniform \\u2014 the prediction set was close to a foregone conclusion, so calibration on it carries little information.",
      "evidence": {
        "outcome_base_rate": 0.9,
        "uncertainty": 0.09,
        "threshold": 0.09
      }
    },
    {
      "code": "INSTANT_VERIFICATION",
      "message": "Most predictions were verified within seconds of being made \\u2014 consistent with 'predicting' answers already known at prediction time.",
      "evidence": {
        "instant_verify_share": 0.7,
        "median_latency_seconds": 53.5,
        "instant_window_seconds": 120.0,
        "threshold": 0.5
      }
    }
  ]
}
```

### Baseline Card: test

```json
{
  "trust_version": "0.1",
  "agent_name": "test",
  "generated": "2026-07-04T01:09:39.431900+00:00",
  "calibration": {
    "total_predictions": 88,
    "total_verified": 88,
    "overall_accuracy": 0.773,
    "mean_confidence": 0.707,
    "mean_calibration_gap": -0.046,
    "confidence_buckets": {
      "50-59": {
        "predictions": 5,
        "correct": 3,
        "accuracy": 0.6,
        "calibration_gap": -0.055,
        "significant": false
      },
      "60-69": {
        "predictions": 29,
        "correct": 18,
        "accuracy": 0.621,
        "calibration_gap": 0.024,
        "significant": false
      },
      "70-79": {
        "predictions": 32,
        "correct": 27,
        "accuracy": 0.844,
        "calibration_gap": -0.099,
        "significant": false
      },
      "80-89": {
        "predictions": 21,
        "correct": 19,
        "accuracy": 0.905,
        "calibration_gap": -0.06,
        "significant": false
      },
      "90-99": {
        "predictions": 1,
        "correct": 1,
        "accuracy": 1.0,
        "calibration_gap": -0.055,
        "insufficient_data": true
      }
    },
    "domains": {
      "architecture": {
        "predictions": 21,
        "correct": 17,
        "avg_confidence": 0.698,
        "accuracy": 0.81
      },
      "behavior": {
        "predictions": 30,
        "correct": 20,
        "avg_confidence": 0.7,
        "accuracy": 0.667
      },
      "codebase": {
        "predictions": 25,
        "correct": 19,
        "avg_confidence": 0.706,
        "accuracy": 0.76
      },
      "facts": {
        "predictions": 3,
        "correct": 3,
        "avg_confidence": 0.8,
        "accuracy": 1.0
      },
      "self": {
        "predictions": 5,
        "correct": 5,
        "avg_confidence": 0.74,
        "accuracy": 1.0
      },
      "tooling": {
        "predictions": 4,
        "correct": 4,
        "avg_confidence": 0.7,
        "accuracy": 1.0
      }
    }
  }
}
```

### Baseline Integrity: test

```json
{
  "agent_name": "test",
  "generated": "2026-07-04T01:09:39.521772+00:00",
  "n_verified": 88,
  "verdict": "1 gaming signature(s) detected in 88 verified predictions.",
  "metrics": {
    "brier_score": 0.1635,
    "reliability": 0.0118,
    "resolution": 0.0239,
    "uncertainty": 0.1756,
    "outcome_base_rate": 0.7727,
    "top_bucket_share": 0.0114,
    "confidence_entropy": 0.8012,
    "domain_hhi": 0.2603,
    "duplicate_claim_ratio": 0.0,
    "template_claim_ratio": 0.0,
    "import_share": 1.0,
    "mendel_p_low": 0.6631,
    "mendel_chi2": 3.3796,
    "mendel_buckets": 3
  },
  "flags": [
    {
      "code": "UNWITNESSED_HISTORY",
      "message": "Most of the record arrived as batch imports with no witnessed gap between prediction and outcome \\u2014 timing cannot be independently trusted.",
      "evidence": {
        "import_share": 1.0,
        "threshold": 0.8
      }
    }
  ]
}
```

### Baseline Card Artifact Drift

`trust-card-claude-opus.json` currently contains 59 verified predictions, not
the 77-prediction card described in `README.md`.

It also contains the D1 defect signature:

```json
"strength_zones": [
  "50-59"
]
```

The `50-59` bucket has only 3 predictions in this artifact, so Phase 1 must
remove this zone after the significance-gating fix.

### Baseline Integrity: claude-trader

`claude-trader` has no verified predictions; `card` correctly fails and
`integrity` reports no analyzable data.

```json
{
  "agent_name": "claude-trader",
  "generated": "2026-07-04T01:09:51.651057+00:00",
  "n_verified": 0,
  "verdict": "No verified predictions \\u2014 nothing to analyze.",
  "insufficient_data": true,
  "flags": []
}
```

### Phase 0 Gate Status

- Tests green: yes, 143 passed.
- Baseline outputs recorded: yes, for `default`, `test`, and `claude-trader`;
  plus `trust-card-claude-opus.json` drift noted.
- Notebook exists: yes, `lab/NOTEBOOK.md`.

Next phase: Phase 1 statistical core, starting with D1/D2 because they change
the card schema/semantics that later intervals and README examples depend on.

## EXP-001 - Phase 1 D1 Insufficient-Data Zone Gating

Hypothesis: zone detection currently treats `BucketStats.significant is None`
as permission to flag danger/strength zones, which means too little data can
produce a stronger claim than enough data. If zone detection requires
`significant is True`, 3-4 prediction buckets with large gaps will stop
flagging, while large tested buckets will still flag.

Mini-plan:

1. Change only `TrustCard.from_predictions` zone gating in `caliber/card.py`.
2. Update card tests so 3-4 sample buckets are explicitly not zones.
3. Keep positive zone tests using larger samples that satisfy the significance
   test.
4. Run the targeted card tests, then the full suite.

Result:

```text
$ python3 -m pytest tests/test_card.py -q
.............................                                            [100%]
29 passed in 0.13s
```

```text
$ python3 -m pytest -q
........................................................................ [ 49%]
........................................................................ [ 99%]
.                                                                        [100%]
145 passed in 1.51s
```

Decision: D1 fixed as a narrow chunk. `TrustCard.from_predictions` now only
creates a danger/strength zone when `BucketStats.significant is True`; an
untestable gap (`None`) is no longer enough. Added explicit 4-sample
regressions for both danger and strength zones.

## EXP-002 - Phase 1 D2 Mean Stated Confidence Per Bucket

Hypothesis: fixed confidence buckets should use the actual mean stated
confidence of predictions inside each bucket as the expected accuracy. Bucket
midpoints are only bin labels; using them as the expectation injects binning
bias into `calibration_gap` and `significant`.

Mini-plan:

1. Add per-bucket `mean_confidence` to `BucketStats`.
2. Make `expected_accuracy` use `mean_confidence` when available.
3. Populate `mean_confidence` in `TrustCard.from_predictions`.
4. Add a regression where a 70% bucket is perfectly calibrated at 0.70 but
   would look miscalibrated against the 0.745 midpoint.
5. Run targeted card tests, real-card smoke commands, then the full suite.

Result:

```text
$ python3 -m pytest tests/test_card.py -q
...............................                                          [100%]
31 passed in 0.14s
```

```text
$ python3 -m pytest -q
........................................................................ [ 48%]
........................................................................ [ 97%]
...                                                                      [100%]
147 passed in 1.75s
```

Real-corpus smoke deltas:

- `default` mean calibration gap changed from `-0.105` to `-0.125`.
- `test` mean calibration gap changed from `-0.046` to `-0.066`.
- Fixed-bucket JSON now carries `mean_confidence` per bucket.
- No new danger/strength zones appeared in either current real corpus.

Decision: D2 fixed for fixed-bucket card generation. Bucket labels remain the
same for compatibility, but `calibration_gap` and `significant` now use the
bucket's observed mean stated confidence when the card is generated from
predictions.

## EXP-003 - Phase 1 D3 Wilson Bucket Intervals

Hypothesis: bucket accuracies as point estimates overstate certainty,
especially for small buckets. Wilson 95% intervals make uncertainty explicit
without adding runtime dependencies.

Mini-plan:

1. Add a Wilson score `ci95` property to `BucketStats`.
2. Emit `ci95: [lo, hi]` in bucket JSON for non-empty buckets.
3. Render the interval in the human Trust Card summary.
4. Add tests for empty buckets, known interval range, JSON emission, and
   summary rendering.
5. Run targeted card tests and the full suite.

Result:

```text
$ python3 -m pytest tests/test_card.py -q
.................................                                        [100%]
33 passed in 0.18s
```

```text
$ python3 -m pytest -q
........................................................................ [ 48%]
........................................................................ [ 96%]
.....                                                                    [100%]
149 passed in 1.73s
```

Real-corpus smoke:

- `python3 -m caliber.cli -a test card --json` now emits `ci95` for every
  non-empty confidence bucket.
- `python3 -m caliber.cli -a test card` renders `95% CI` in the human summary.

Decision: D3 fixed for fixed buckets. Wilson intervals make small-bucket
uncertainty explicit, including visibly wide intervals such as the 1-sample
`90-99` bucket (`20.7%-100.0%` in the current `test` corpus).

## EXP-004 - Phase 1 D4 Exact Binomial Significance

Hypothesis: the current normal approximation can misstate bucket significance
near the small-sample threshold. An exact two-sided binomial test keeps the
same public `significant` field but removes the approximation error. The D1
minimum-data gate remains: buckets with fewer than 5 predictions still return
`None`.

Mini-plan:

1. Add a stdlib-only exact two-sided binomial helper using `math.lgamma`.
2. Replace the normal approximation inside `BucketStats.significant`.
3. Add a known-value test for k=9, n=10, p0=0.5 -> p ~= 0.021484.
4. Run targeted card tests and the full suite.

Result:

```text
$ python3 -m pytest tests/test_card.py -q
..................................                                       [100%]
34 passed in 0.15s
```

```text
$ python3 -m pytest -q
........................................................................ [ 48%]
........................................................................ [ 96%]
......                                                                   [100%]
150 passed in 1.54s
```

Real-corpus smoke:

- `default` and `test` card significance flags stayed stable under the exact
  test in current data.
- Added known-value regression: `P(X as or more unlikely than 9 successes out
  of 10 at p0=0.5) = 0.021484375`.

Decision: D4 fixed for bucket significance. The public `significant` field is
unchanged, but now comes from an exact binomial test for n >= 5 instead of the
normal approximation.

## EXP-005 - Phase 1 Card-Level Proper Scores

Hypothesis: Trust Cards should expose card-level scoring and binning-free
calibration statistics, not only bucket tables. Brier/Murphy decomposition
shows reliability, resolution, and uncertainty; Spiegelhalter Z tests
aggregate miscalibration without depending on buckets.

Mini-plan:

1. Add card-local helpers for Murphy decomposition and Spiegelhalter Z.
2. Add `brier_score`, `reliability`, `resolution`, `uncertainty`,
   `calibration_z`, and `calibration_p` fields to `TrustCard`.
3. Emit these fields in Trust Card JSON and human summary.
4. Add deterministic tests for a perfectly calibrated one-forecast stream.
5. Run targeted card tests and the full suite.

Result:

```text
$ python3 -m pytest tests/test_card.py -q
....................................                                     [100%]
36 passed in 0.15s
```

```text
$ python3 -m pytest -q
........................................................................ [ 47%]
........................................................................ [ 94%]
........                                                                 [100%]
152 passed in 1.68s
```

Real-corpus smoke:

- `test` Trust Card JSON now includes `brier_score`, `reliability`,
  `resolution`, `uncertainty`, `calibration_z`, and `calibration_p`.
- Current `test` values: Brier `0.1635`, reliability `0.0118`,
  resolution `0.0239`, uncertainty `0.1756`, calibration_z `1.3861`,
  calibration_p `0.1657`.
- Human summary renders the same Brier decomposition and Z result.

Decision: card-level proper-score fields are surfaced on Trust Cards. This
makes the card more comparable to the integrity report and gives a
binning-free calibration test alongside the bucket table.

## EXP-006 - Phase 1 Adaptive Equal-Mass Buckets

Hypothesis: fixed buckets are useful for compatibility, but they can hide or
exaggerate calibration patterns when data clusters unevenly. Equal-mass
adaptive buckets expose calibration with less binning bias while leaving the
fixed buckets intact for existing consumers.

Mini-plan:

1. Add an adaptive bucket stats type with confidence range, mean confidence,
   accuracy, and Wilson interval.
2. Build adaptive buckets by sorting verified predictions by confidence and
   cutting them into `max(3, ceil(n/25))` near-equal non-empty groups.
3. Emit `adaptive_buckets` in Trust Card JSON and render them in the summary.
4. Add tests for bucket count, equal-mass shape, JSON fields, and summary text.
5. Run targeted card tests and the full suite.

Result:

```text
$ python3 -m pytest tests/test_card.py -q
.......................................                                  [100%]
39 passed in 0.19s
```

```text
$ python3 -m pytest -q
........................................................................ [ 46%]
........................................................................ [ 92%]
...........                                                              [100%]
155 passed in 1.99s
```

Real-corpus smoke:

- Current `test` corpus now emits four adaptive buckets of 22 predictions each.
- The adaptive view exposes a clearer low-confidence underperformance/upper
  confidence underconfidence pattern:
  - bucket 1: 50.0% accuracy, mean confidence 59.5%;
  - bucket 2: 77.3% accuracy, mean confidence 67.3%;
  - bucket 3: 90.9% accuracy, mean confidence 72.7%;
  - bucket 4: 90.9% accuracy, mean confidence 83.2%.

Decision: adaptive buckets are added as a second view without removing or
renaming the fixed five-bucket table, preserving compatibility.

## EXP-007 - Phase 1 Property-Based Statistical Invariants

Hypothesis: the new statistical helpers should be protected by invariant-style
tests, not only hand-picked examples. Hypothesis can generate random forecast
streams for Murphy identity checks, while deterministic Monte Carlo coverage
can guard Wilson intervals across the NORTHSTAR grid.

Mini-plan:

1. Add `hypothesis` under `[project.optional-dependencies].dev` only; do not
   add any runtime dependency.
2. Add a focused property test file for Murphy identity, Wilson interval
   coverage, and exact-binomial known values/properties.
3. Keep Monte Carlo deterministic and bounded so the full suite stays fast.
4. Install the dev extra locally only if needed for verification.
5. Run the new property tests, then the full suite.

Result:

Initial setup findings:

- `python3 -m pip install -e .[dev]` against system Python failed with
  PEP 668 `externally-managed-environment`; verification moved to disposable
  venv `/tmp/caliber-northstar-p1-properties`.
- The first venv install failed under sandbox DNS while fetching build
  dependencies, then succeeded after explicit network approval.
- Existing `tests/test_mcp_server.py` imports `mcp`, so the new `dev` extra
  must include the existing MCP optional dependency for a fresh full-suite run.
  CI was updated to install `.[dev]`.

First property-test run failed usefully:

- Hypothesis rejected `width=32` floats with bounds `0.001`/`0.999` because
  those exact decimals are not representable as 32-bit floats. Fix: use default
  64-bit float generation.
- Wilson intervals for zero successes can produce a tiny positive lower bound
  (`5.55e-17`) instead of mathematical zero. Fix: clamp near-zero and near-one
  numerical artifacts inside `_wilson_ci`.

Wilson coverage check:

Exact enumeration over the NORTHSTAR grid showed the requested "93-97%
coverage for every Wilson cell" is mathematically false for this interval at
small n/extreme p. The test now pins the actual exact coverage values and
records the cells outside the original band:

```text
(5, 0.85)=0.9734
(5, 0.95)=0.9774
(10, 0.70)=0.9244
(10, 0.95)=0.9139
(20, 0.70)=0.9752
(20, 0.85)=0.9781
(20, 0.95)=0.9245
```

Verification:

```text
$ /tmp/caliber-northstar-p1-properties/bin/python -m pytest tests/test_card_properties.py -q
......                                                                   [100%]
6 passed in 1.97s
```

```text
$ /tmp/caliber-northstar-p1-properties/bin/python -m pytest -q
........................................................................ [ 44%]
........................................................................ [ 89%]
.................                                                        [100%]
161 passed in 4.04s
```

LRN: A nominal 95% Wilson interval does not guarantee 93-97% exact coverage
on every small-sample grid cell. Future statistical gates should prefer exact
enumeration for binomial intervals when n is small, and treat Monte Carlo as a
smoke check against the exact result, not as the source of truth.

Decision: property/invariant tests are added with Hypothesis as a dev-only
dependency. The literal Wilson acceptance band from NORTHSTAR is corrected by
evidence rather than forced into a misleading test.

## EXP-008 - Phase 1 Regenerate Flagship Trust Card

Hypothesis: regenerating `trust-card-claude-opus.json` with the corrected
card statistics should remove the old small-sample `strength_zones` claim,
surface the new uncertainty/proper-score/adaptive-bucket fields, and force the
README interpretation to match current evidence.

Mini-plan:

1. Make the compatibility wrapper import MY UNIVERSE calibration data through
   in-memory storage so regeneration does not mutate `~/.caliber`.
2. Regenerate `trust-card-claude-opus.json` from
   `/home/satishocoin/MY UNIVERSE/CALIBRATE.md`.
3. Update the README's embedded Trust Card excerpt and interpretation
   paragraph with current values and no small-sample zone claim.
4. Run wrapper/README-adjacent tests, then the full dev-venv suite.

Result:

Regeneration command:

```text
$ python3 extract_calibrate_md.py
Reading: /home/satishocoin/MY UNIVERSE/CALIBRATE.md
Parsed: 94 verified predictions
...
Trust Card saved: /home/satishocoin/caliber/trust-card-claude-opus.json
```

Key regenerated card values:

- 94 verified predictions, 75.5% accuracy, 70.7% mean confidence.
- Mean calibration gap changed to `-0.048` under the corrected mean-confidence
  bucket definition.
- Brier `0.1798`; reliability `0.0205`; resolution `0.0255`;
  uncertainty `0.1848`; calibration Z `1.0537`, p `0.292`.
- No `danger_zones` or `strength_zones` fields remain in the artifact.
- The 90-99 bucket has a large apparent overconfidence gap (`0.425`) but only
  2 predictions, so it is `insufficient_data`, not a zone.
- Four adaptive buckets are present: 23/24/23/24 predictions.

README/artifact checks:

```text
$ python3 - <<'PY'
...
README excerpt and artifact consistency checks passed
PY
```

Wrapper and store-boundary checks:

```text
$ python3 -m pytest tests/test_extract_calibrate_md.py -q
.                                                                        [100%]
1 passed in 0.08s
```

```text
$ test ! -e /home/satishocoin/.caliber/claude-opus-my-universe.json
# exit 0
```

Full suite:

```text
$ /tmp/caliber-northstar-p1-properties/bin/python -m pytest -q
........................................................................ [ 44%]
........................................................................ [ 89%]
.................                                                        [100%]
161 passed in 4.03s
```

Decision: the flagship card and README interpretation are now grounded in the
current source corpus and corrected card statistics. The compatibility wrapper
now uses `MemoryStorage`, so regenerating the repo artifact does not pollute
the user's global Caliber store.

## Phase 1 Gate - Statistical Core

Date: 2026-07-04

Gate evidence:

- D1 fixed: zones require `significant is True`; insufficient data no longer
  permits zone claims.
- D2 fixed: fixed-bucket `calibration_gap` uses mean stated confidence instead
  of bucket midpoint when generated from prediction streams.
- D3 fixed: fixed and adaptive buckets carry Wilson 95% intervals.
- D4 fixed: bucket significance uses exact two-sided binomial p-values.
- Card-level Brier/Murphy and Spiegelhalter Z are exposed in JSON and summary.
- Adaptive equal-mass buckets are added as a second view; fixed buckets remain
  backward compatible.
- Property/invariant tests are added under the `dev` extra; full suite is
  161 passing in a fresh dev venv.
- `trust-card-claude-opus.json` is regenerated from the current source corpus;
  no small-sample zone claim remains.
- README card excerpt and interpretation match the regenerated artifact.

Meta-checkpoint:

1. Re-read §0. Phase 1 increased honesty, not just complexity: every added
   field either reduces estimator bias, exposes uncertainty, tests an
   invariant, or removes an overclaim.
2. Last reality check: full dev-venv suite `161 passed in 4.03s`, wrapper test
   `1 passed`, README JSON excerpt parsed, and regenerated artifact checked
   for no `strength_zones`.
3. Result that was too clean: the original Wilson coverage target. Exact
   enumeration disproved the 93-97% band for several small-n/extreme-p cells.
   The test now records the true coverage table instead of forcing a fake pass.
4. Asked question vs easier one: the easier answer would have been to add
   Hypothesis tests that pass without challenging the coverage requirement.
   The actual answer corrected the requirement with computed evidence.

Phase 1 decision: gate accepted with one documented correction to NORTHSTAR's
coverage-test acceptance band. Next phase is Phase 2 Adversarial Lab.

## EXP-009 - Phase 2 Simulator Zoo

Hypothesis: before threshold benchmarking, Caliber needs deterministic
population generators whose outputs can be converted directly into
`Prediction` objects and fed through `IntegrityReport`. The simulator layer
should make honest streams, known attackers, and known impossibility cases
reproducible by `(n, seed)`.

Mini-plan:

1. Add `lab/simulate.py` with stdlib-only generators for the required
   NORTHSTAR population zoo.
2. Return `Prediction`-compatible dictionaries and provide a `to_predictions`
   helper for tests/bench code.
3. Add focused simulator tests for determinism, schema compatibility, and
   expected current integrity flags on representative populations.
4. Keep this chunk to simulation only; full FPR/power benchmarking belongs to
   the next `lab/run_bench.py` chunk.
5. Run simulator tests and the full dev-venv suite.

Result:

Added:

- `lab/simulate.py`
- `lab/__init__.py`
- `tests/test_lab_simulate.py`

Simulator coverage:

- `honest(sharpness)`
- `overconfident(delta)`
- `underconfident(delta)`
- `noisy(sigma)`
- `farmer(easy_share)`
- `patient_farmer(easy_share)`
- `naive_fabricator`
- `smart_fabricator`
- `template_spammer`
- `domain_camper(k_domains)`
- `bulk_importer(import_share)`
- `mixture(honest_frac, attacker, ...)`

Representative flag smoke at n=120, seed=42:

```text
honest: flags=[]
farmer: flags=['LOW_OUTCOME_VARIANCE', 'CONFIDENCE_CONCENTRATION', 'DOMAIN_CONCENTRATION', 'INSTANT_VERIFICATION']
patient_farmer: flags=['LOW_OUTCOME_VARIANCE', 'CONFIDENCE_CONCENTRATION', 'DOMAIN_CONCENTRATION']
naive_fabricator: flags=['NO_DISCRIMINATION', 'SUSPICIOUSLY_PERFECT']
smart_fabricator: flags=[]
domain_camper: flags=['DOMAIN_CONCENTRATION']
bulk_importer: flags=['UNWITNESSED_HISTORY']
```

Verification:

```text
$ /tmp/caliber-northstar-p1-properties/bin/python -m pytest tests/test_lab_simulate.py -q
.........                                                                [100%]
9 passed in 0.91s
```

```text
$ /tmp/caliber-northstar-p1-properties/bin/python -m pytest -q
........................................................................ [ 42%]
........................................................................ [ 84%]
..........................                                               [100%]
170 passed in 4.02s
```

Decision: simulator zoo chunk is complete. It provides deterministic inputs
for the next benchmark harness, but does not yet estimate FPR/power or change
any integrity threshold.

## EXP-010 - Phase 2 Benchmark Harness

Hypothesis: a deterministic benchmark runner can convert the simulator zoo
into measurable per-flag firing rates by population and sample size. The first
chunk should add the harness and fast regression tests; the full 500-replicate
bench should be run after the harness is committed so result files can cite a
stable code SHA.

Mini-plan:

1. Add `lab/run_bench.py` with a reusable `run_bench()` function and CLI.
2. Cover populations x n-grid x replicates, computing `any_flag` and per-flag
   firing rates from `IntegrityReport`.
3. Emit JSON under `lab/results/bench-<sha>.json` and Markdown summary at
   `lab/REPORT.md` when requested.
4. Add fast tests with small replicate counts to prove determinism and output
   shape without running the full bench.
5. Run harness tests and the full dev-venv suite; full 500-replicate bench is
   the next chunk.

Result:

Added:

- `lab/run_bench.py`
- `tests/test_lab_run_bench.py`

Smoke-test failures and fixes:

- Direct execution failed first: `python lab/run_bench.py ...` could not import
  `lab` because Python put `lab/` on `sys.path`. Fix: when run as a script,
  prepend repo root to `sys.path`.
- No-write CLI smoke exposed bad simulator baselines: honest streams initially
  had high `template_claim_ratio`, then high `duplicate_claim_ratio`, because
  claim text repeated too much. Fix: honest and smart-fabricator claims now use
  varied nonnumeric marker/path tokens, leaving template spam visible only in
  the intended populations.

Tiny no-write CLI smoke:

```text
$ /tmp/caliber-northstar-p1-properties/bin/python lab/run_bench.py --replicates 2 --sample-size 20 --no-write
...
honest: any_flag_rate=0.0, template_claim_ratio=0.0
smart_fabricator: any_flag_rate=0.0, template_claim_ratio=0.0
farmer: any_flag_rate=1.0
```

Verification:

```text
$ /tmp/caliber-northstar-p1-properties/bin/python -m pytest tests/test_lab_simulate.py tests/test_lab_run_bench.py -q
............                                                             [100%]
12 passed in 0.90s
```

```text
$ /tmp/caliber-northstar-p1-properties/bin/python -m pytest -q
........................................................................ [ 41%]
........................................................................ [ 83%]
.............................                                            [100%]
173 passed in 6.15s
```

Decision: benchmark harness chunk is ready to commit. It can emit JSON and
Markdown artifacts, but the full 500-replicate bench is intentionally the next
chunk so the result can cite this committed harness SHA.

## EXP-011 - Phase 2 Full 500-Replicate Benchmark Run

Hypothesis: the committed benchmark harness can run the full NORTHSTAR grid
(required populations x n={20,50,100,300} x 500 replicates) within the target
runtime and emit durable JSON/Markdown artifacts for threshold analysis.

Mini-plan:

1. Run `lab/run_bench.py` with default 500 replicates from committed harness
   SHA `e9b87f6`.
2. Save JSON under `lab/results/bench-e9b87f6.json` and update
   `lab/REPORT.md`.
3. Inspect headline honest false-positive and attacker detection rates.
4. Record runtime, result paths, and immediate failures/threshold concerns in
   the notebook.
5. Run the full dev-venv suite after artifact generation.

Result:

First timing attempt:

```text
$ /usr/bin/time -f "elapsed_seconds=%e" /tmp/caliber-northstar-p1-properties/bin/python lab/run_bench.py
/bin/bash: line 1: /usr/bin/time: No such file or directory
```

Rerun used a Python `time.perf_counter()` wrapper around the committed harness.

```text
Wrote /home/satishocoin/caliber/lab/results/bench-e9b87f6.json
Wrote /home/satishocoin/caliber/lab/REPORT.md
elapsed_seconds=234.98
```

Artifacts:

- `lab/results/bench-e9b87f6.json` (36K)
- `lab/REPORT.md` (8K)
- 44 rows: 11 populations x 4 sample sizes.
- 500 replicates per cell.

Headline n=50/n=100 rates:

```text
honest n=50 any=0.002; n=100 any=0.004
overconfident n=50 any=0.046; n=100 any=0.010
underconfident n=50 any=0.002; n=100 any=0.000
noisy n=50 any=0.014; n=100 any=0.000
farmer n=50 any=1.000; n=100 any=1.000
patient_farmer n=50 any=1.000; n=100 any=1.000
naive_fabricator n=50 any=1.000; n=100 any=1.000
smart_fabricator n=50 any=0.012; n=100 any=0.004
template_spammer n=50 any=0.308; n=100 any=0.318
domain_camper n=50 any=1.000; n=100 any=1.000
bulk_importer n=50 any=1.000; n=100 any=1.000
```

Immediate interpretation:

- The current constants meet the Phase 2 honest FPR target at n=50 for the
  primary honest population (0.2%) and stay below 5% for overconfident,
  underconfident, noisy, and smart-fabricator boundary streams at n=50.
- Farmer and patient farmer are detected with 100% any-flag power at n=50 and
  n=100. Patient farmer correctly avoids `INSTANT_VERIFICATION` but is caught
  by distributional/domain concentration signals.
- Naive fabrication is detected with 100% power at n>=50 by
  `SUSPICIOUSLY_PERFECT` and `NO_DISCRIMINATION`.
- Smart fabrication remains effectively indistinguishable from honest by
  record-only statistics (1.2% any flag at n=50, 0.4% at n=100). This supports
  the threat-model boundary rather than a threshold change.
- Template spammer is not directly flagged for templating; any flags come
  mostly from `NO_DISCRIMINATION`. This matches the current design that
  `template_claim_ratio` is a metric, not a flag.
- At n=20, honest-like populations can exceed 5% any-flag rate due to
  `LOW_OUTCOME_VARIANCE`; Phase 2's threshold target is stated at n=50, but
  the n=20 behavior should be mentioned in `lab/THREATMODEL.md`.

Verification:

```text
$ /tmp/caliber-northstar-p1-properties/bin/python -m pytest -q
........................................................................ [ 41%]
........................................................................ [ 83%]
.............................                                            [100%]
173 passed in 6.75s
```

Decision: the initial full bench is usable evidence for threshold
re-derivation. Next chunk should convert these rates into threshold operating
point comments in `integrity.py` and decide whether any current threshold
actually changes.
