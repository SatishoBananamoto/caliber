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
