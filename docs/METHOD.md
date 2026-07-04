# Caliber Method

Status: Round Two Phase A method paper.

Caliber is a calibration instrument for AI agents. It records stated
confidence, later outcomes, and the evidence shape of the record itself. Its
goal is narrower than "trust": it measures whether confidence claims match
outcomes, then stress-tests the record against known ways to inflate a
calibration track record.

Based on the prior-art set in `NORTHSTAR2.md` section 5, Caliber occupies a
specific empty cell: a released, local tool that checks an agent's longitudinal
calibration record against known gaming strategies and reports measured
detection operating points. That claim is bounded by this paper's limitations:
Caliber does not know semantic task difficulty, does not witness predictions
unless the event log is used before outcomes, and still relies on the recording
party to judge outcomes.

## Problem

Agents state confidence. A code-review agent says it is 80% confident; a
research agent says a citation is 70% likely to support a claim; an operations
agent says a deploy check is 90% safe. Without an outcome ledger, those
confidence statements are ungrounded.

There are two distinct failure modes.

First, an agent can be honestly miscalibrated. It may say 80% while being right
60%, or say 60% while being right 80%. This is a statistical problem.

Second, an agent can inflate its record. It can farm easy predictions, repeat
the same claim, import already-known outcomes, concentrate on one domain, or
fabricate outcomes that fit its stated confidence. This is an adversarial
record problem. Calibration alone is not enough because a record can look
calibrated while carrying little evidence of real predictive skill.

Caliber therefore treats a Trust Card as evidence about a specific record, not
as proof of general competence.

## Related Work

Human prediction journals are mature but not agent-forensics tools. Fatebook
is designed for low-friction human prediction tracking and shows Brier score
and calibration charts. PredictionBook is the older public calibration-journal
line. These tools help people build forecasting track records, but the cited
materials do not present an adversarial benchmark for detecting record
inflation by automated agents.

Agent-calibration research attacks a different primitive. Agentic Confidence
Calibration introduces methods for calibrating confidence during agent tasks.
TrustBench maps stated confidence and trust signals into a real-time action
verification pipeline. Both are about in-the-moment confidence estimation or
action gating. Caliber instead evaluates a longitudinal ledger after outcomes
are recorded.

Adjacent reliability tooling also differs. BayesTruth tracks tool or MCP
server reliability with a Beta-Bernoulli score and hash-chained audit trail.
`mcp-confidence` uses logprob-style confidence to accept, verify, or escalate a
tool result. Those primitives score calls or generated outputs; Caliber scores
whether an agent's stated confidence history was honest and informative.

The gaming theory is directly relevant. Foster and Hart's calibeating line and
the Simons Institute forecast-hedging talk make the central warning explicit:
calibration is gameable, so a useful instrument must also look at resolution,
sharpness, and record provenance. Caliber turns that warning into executable
checks over stored prediction records.

| work area | example sources | primitive | Caliber difference |
| --- | --- | --- | --- |
| Human journals | Fatebook, PredictionBook | Human forecast tracking | Caliber targets automated-agent records and gaming signatures. |
| Agent calibration | Agentic Confidence Calibration, TrustBench | Runtime confidence estimation or action gating | Caliber verifies a historical ledger. |
| Reliability scoring | BayesTruth, `mcp-confidence` | Tool/call reliability or output gating | Caliber tests stated-confidence honesty over outcomes. |
| Gaming theory | Calibeating, forecast hedging | Calibration can be gamed | Caliber implements measured record-level detectors. |

## The Instrument

The source of truth is a sequence of prediction records. A prediction carries
an ID, claim, confidence, domain, timestamp, optional outcome, optional
verification timestamp, notes, and optional commitment fields. Confidence is
bounded to [0.50, 0.99] by `caliber/tracker.py`.

### Bucket Gaps

Caliber reports fixed confidence buckets: 50-59, 60-69, 70-79, 80-89, and
90-99. For a non-empty bucket, expected accuracy is the mean stated confidence
inside that bucket, not the bucket midpoint. The gap is:

```text
calibration_gap = mean_confidence - accuracy
```

Positive means overconfidence; negative means underconfidence.

This choice fixes a round-one defect: comparing to the bucket midpoint injects
up to 5 percentage points of binning bias into every bucket. The current code
uses mean stated confidence in `caliber/card.py`, and the regression test is
`tests/test_card.py::test_bucket_gap_uses_mean_stated_confidence_not_midpoint`.

### Wilson Intervals

Each bucket accuracy is a binomial proportion. Caliber reports a Wilson 95%
interval rather than a bare point estimate. For `k` correct outcomes in `n`
predictions and z = 1.959963984540054:

```text
p_hat = k / n
center = (p_hat + z^2 / (2n)) / (1 + z^2 / n)
half = z * sqrt(p_hat(1 - p_hat) / n + z^2 / (4n^2)) / (1 + z^2 / n)
ci95 = [max(0, center - half), min(1, center + half)]
```

The failure mode is small-sample overclaiming. The flagship card once promoted
a strength zone from 4 predictions because "untestable" was treated as
acceptable evidence. Current cards mark small buckets as `insufficient_data`;
zones require a completed significant test.

### Exact Binomial Tests

A confidence bucket becomes a danger or strength zone only when the absolute
gap is greater than 0.10 and an exact two-sided binomial test returns p < 0.05.
Buckets with fewer than 5 predictions do not run the test.

The test sums the probability of every binomial outcome whose probability mass
is no larger than the observed outcome's probability mass, using log-space
PMFs. This replaces a normal approximation at small n.

The failure mode is false certainty in tiny buckets. The test
`tests/test_card_properties.py::test_exact_binomial_known_values` pins known
values, including `k=9, n=10, p0=0.5 -> p=0.021484375`.

### Spiegelhalter's Z

Bucket tests are useful for explanation, but binning can hide global
miscalibration. Caliber also reports Spiegelhalter's Z over all verified
predictions:

```text
Z = sum(outcome_i - confidence_i) / sqrt(sum(confidence_i * (1 - confidence_i)))
```

The two-sided p-value comes from the standard normal CDF implemented with
`math.erfc`, avoiding a runtime SciPy dependency.

### Brier Score And Murphy Decomposition

Caliber reports the Brier score and Murphy decomposition:

```text
Brier = reliability - resolution + uncertainty
```

Reliability is the calibration term. Resolution measures whether confidence
levels discriminate between outcomes. Uncertainty is the variance of the
outcome base rate. This matters because a trivial-prediction farmer can make
reliability look good while destroying resolution or uncertainty.

The property test
`tests/test_card_properties.py::test_murphy_identity_holds_for_random_streams`
checks the identity to `1e-9` on random forecast streams.

### Adaptive Buckets

Fixed buckets are stable and readable, but they can be sparse. Caliber also
reports equal-mass adaptive buckets. It sorts verified predictions by
confidence and cuts them into `ceil(n / 25)` near-equal groups with a minimum
of 3 groups. Each adaptive bucket reports confidence range, mean confidence,
accuracy, Wilson interval, and calibration gap.

The failure mode is fixed-bucket sparsity. Adaptive buckets do not replace the
fixed schema; they provide a second view when the record is large enough.

## The Adversarial Benchmark

The adversarial lab in `lab/run_bench.py` simulates a population zoo and
measures which integrity flags fire. The full bench uses 500 deterministic
replicates per cell and sample sizes n in {20, 50, 100, 300}. The rendered
artifact is `lab/REPORT.md`; the JSON artifact is
`lab/results/bench-08b2cff.json` with 48 rows.

The populations are:

- clean or low-quality but non-adversarial probes: honest, overconfident,
  underconfident, noisy;
- record-inflation probes: farmer, patient farmer, naive fabricator, template
  spammer, duplicate spammer, domain camper, bulk importer;
- boundary probe: smart fabricator;
- mixtures are supported by `lab/simulate.py` for partial-gaming experiments.

Clean and boundary rates below are `any_flag` rates from the full bench:

| population | n=50 | n=100 | interpretation |
| --- | ---: | ---: | --- |
| honest | 2.8% | 1.0% | Calibrated Bernoulli record stays under the per-flag false-positive budget. |
| overconfident | 7.2% | 1.4% | Biased forecasters can trip some evidence; flags stay separate rather than becoming one score. |
| underconfident | 3.0% | 1.4% | Underconfidence is not automatically treated as gaming. |
| noisy | 4.2% | 1.0% | Weak discrimination alone is not enough unless thresholds fire. |
| smart_fabricator | 4.6% | 1.4% | Statistically plausible fabrication is record-only indistinguishable from honest data. |

Attack detection rates below are also from the full bench:

| attack population | primary signal | n=50 | n=100 |
| --- | --- | ---: | ---: |
| farmer | Low outcome variance, confidence concentration, domain concentration, instant verification | 100.0% | 100.0% |
| patient farmer | Low outcome variance, confidence concentration, domain concentration | 100.0% | 100.0% |
| naive fabricator | No discrimination, suspiciously perfect outcomes | 100.0% | 100.0% |
| template spammer | No discrimination | 100.0% | 100.0% |
| duplicate spammer | Duplicate claims | 100.0% | 100.0% |
| domain camper | Domain concentration | 100.0% | 100.0% |
| bulk importer | Unwitnessed history | 100.0% | 100.0% |

Thresholds were re-derived by `lab/analyze_thresholds.py` at n=50 with 500
replicates. Each threshold is chosen to keep clean per-flag false-positive rate
at or below 5% while maximizing target-attacker power. The rendered artifact is
`lab/THRESHOLDS.md`; `caliber/integrity.py` carries the measured operating
point next to each threshold constant.

The threshold table is:

| constant | value | clean FPR | target power |
| --- | ---: | ---: | --- |
| LOW_UNCERTAINTY_THRESHOLD | 0.13 | 3.6% | 99.5% mean against farmer and patient farmer |
| LOW_RESOLUTION_RATIO | 0.4945 | 0.4% | 100.0% against naive fabricator and template spammer |
| TOP_BUCKET_SHARE_THRESHOLD | 0.6 | 0.6% | 100.0% against farmer and patient farmer |
| DOMAIN_HHI_THRESHOLD | 0.6 | 0.0% | 100.0% against domain camper |
| DUPLICATE_RATIO_THRESHOLD | 0.2 | 0.0% | 100.0% against duplicate spammer |
| INSTANT_SHARE_THRESHOLD | 0.5 | 0.0% | 100.0% against farmer |
| IMPORT_SHARE_THRESHOLD | 0.8 | 0.0% | 100.0% against bulk importer |
| MENDEL_P_LOW_THRESHOLD | 0.01 | 0.0% | 100.0% against naive fabricator |

The benchmark is deliberately not collapsed into an aggregate integrity score.
An aggregate would become the next gaming target and would hide the difference
between small-sample noise, biased but honest forecasting, and adversarial
record shape.

## Threat Model And Impossibility Boundary

Caliber's record-only checks can detect suspicious shapes in the stored
prediction record: low outcome variance, no discrimination, confidence
concentration, domain concentration, duplicate claims, instant verification,
unwitnessed import history, and suspiciously perfect bucket-level outcomes.

The patient-farmer result is the best example. A patient farmer waits out the
instant-verification window, so latency alone cannot catch it. The bench still
detects it at 100.0% for n=50 and n=100 because low outcome variance,
confidence concentration, and domain concentration remain visible.

There are hard limits.

Smart fabrication is undetectable from the record alone when the fabricated
record samples outcomes from Bernoulli(confidence), uses varied claims and
domains, and uses plausible latencies. In the bench, `smart_fabricator@n=50`
had a 4.6% any-flag rate and `smart_fabricator@n=100` had a 1.4% rate, close
to clean populations. That is not a bug; it is an information boundary.

Synthetic import timestamps are also not fixable from mutable JSON alone. An
attacker who can write the store can invent plausible non-equal verification
times. The Phase 3 event log records event origins and hash-chains events, but
third-party proof still requires a witnessed or externally anchored head.

Semantic difficulty is outside the record. Caliber can see distributions, not
meaning. It cannot prove that a prediction was important, hard,
independently judged, or non-trivial. Claim-text judging is deliberately not
used because it would be language-dependent and gameable.

Evidence levels are:

| evidence level | what it supports | what it does not support |
| --- | --- | --- |
| Record only | Calibration statistics and distributional gaming signatures | Timing proof, semantic difficulty, independent outcome truth |
| Witnessed timing | Stronger evidence that prediction preceded outcome | Retroactive history proof unless the witness is durable |
| Anchored history | Third parties can detect rewrites after a saved chain head | Truth of the outcome label |
| External adjudication | Stronger ground-truth and difficulty evidence | Perfect protection against colluding adjudicators |

## Limitations

Self-adjudication is the main limitation. Outcomes are currently recorded by
the same party that made the predictions. `verify-card` can recompute a saved
card from the event log, but it cannot decide whether a human or agent judged
the outcome honestly.

Unwitnessed imports remain weak evidence. Migrated legacy JSON records are
marked as imported history; the chain proves future ordering, not the original
timing of pre-migration predictions.

Manual anchoring is required. `caliber anchor` prints and appends chain heads,
but Caliber does not publish them to a timestamping service or registry.

Scope is single-agent and binary-outcome only. Multi-agent comparison,
multi-class outcomes, signed cards, and third-party adjudication are future
work, not present claims.

## Reproduction

Use the existing development environment if available:

```bash
/tmp/caliber-northstar-p1-properties/bin/python -m pytest -q
/tmp/caliber-northstar-p1-properties/bin/python -m compileall -q caliber
```

If that environment is broken, create a disposable environment under `/tmp`:

```bash
python3 -m venv /tmp/caliber-method-repro
/tmp/caliber-method-repro/bin/python -m pip install -e . hypothesis pytest mcp
```

Run the full benchmark and render `lab/REPORT.md`:

```bash
/tmp/caliber-northstar-p1-properties/bin/python lab/run_bench.py
```

Recompute threshold operating points and render `lab/THRESHOLDS.md`:

```bash
/tmp/caliber-northstar-p1-properties/bin/python lab/analyze_thresholds.py
```

Run the fast benchmark regression:

```bash
/tmp/caliber-northstar-p1-properties/bin/python -m pytest tests/test_lab_bench.py -q
```

Run the tamper-evidence and card-verification tests:

```bash
/tmp/caliber-northstar-p1-properties/bin/python -m pytest tests/test_event_log.py tests/test_storage.py tests/test_cli.py -q
```

Regenerate a Trust Card from an event-log-backed store:

```bash
STORE=$(mktemp -d /tmp/caliber-method-card.XXXXXX)
AGENT=method-demo
caliber --agent "$AGENT" --store "$STORE" predict "the demo store exists" --confidence 80 --domain demo --id demo-1
caliber --agent "$AGENT" --store "$STORE" verify demo-1 --correct
caliber --agent "$AGENT" --store "$STORE" card --json > /tmp/method-card.json
caliber --agent "$AGENT" --store "$STORE" verify-log
caliber --agent "$AGENT" --store "$STORE" verify-card /tmp/method-card.json
```

The store path above is created under `/tmp`; do not run destructive cleanup
commands against project files.

## Numeric Claim Source Map

| number or range | claim | source |
| --- | --- | --- |
| section 5 | Prior-art citation set | `NORTHSTAR2.md` section 5 |
| 80%, 70%, 90%, 60% | Illustrative confidence examples, not empirical results | Problem-statement examples in this document |
| 0.50, 0.99 | Allowed confidence bounds | `caliber/tracker.py::_validate_confidence` |
| 50-59 through 90-99 | Fixed bucket labels | `caliber/card.py::BUCKET_RANGES` |
| 2, 4, and exponents in formulas | Algebraic terms in Wilson and Brier formulas | `NORTHSTAR.md` section 5 formulas, `caliber/card.py` |
| 0.10, 0.05, 5 | Zone gap, significance, and minimum bucket test size | `caliber/card.py::TrustCard.from_predictions`, `BucketStats.significant` |
| 1.959963984540054, 95% | Wilson interval constant and label | `caliber/card.py::WILSON_Z_95`, `BucketStats.ci95` |
| 4 | Former insufficient-data zone example | `NORTHSTAR.md` section 2 defect D1 and `NORTHSTAR2.md` section 3 A1 |
| 5 percentage points | Midpoint binning-bias bound | `NORTHSTAR2.md` section 3 A1 and `NORTHSTAR.md` section 2 defect D2 |
| 9, 10, 0.5, 0.021484375 | Exact binomial pinned value | `tests/test_card_properties.py::test_exact_binomial_known_values` |
| 1e-9 | Murphy identity property tolerance | `tests/test_card_properties.py::test_murphy_identity_holds_for_random_streams` |
| 25, 3 | Adaptive bucket divisor and minimum groups | `caliber/card.py::_build_adaptive_buckets` |
| 500, 20, 50, 100, 300, 48 | Full benchmark shape | `lab/REPORT.md`, `lab/results/bench-08b2cff.json`, `lab/run_bench.py` |
| 2.8%, 1.0%, 7.2%, 1.4%, 3.0%, 4.2%, 4.6% | Clean and boundary any-flag rates | `lab/REPORT.md` |
| 100.0% attack rates | Attack detection rates | `lab/REPORT.md`, `lab/THREATMODEL.md` |
| 0.13, 0.4945, 0.6, 0.2, 0.5, 0.8, 0.01 | Integrity threshold values | `lab/THRESHOLDS.md`, `caliber/integrity.py` |
| 3.6%, 0.4%, 0.6%, 0.0%, 99.5%, 100.0% | Threshold FPR and power values | `lab/THRESHOLDS.md` |
| 4.6%, 1.4% | Smart-fabricator boundary rates | `lab/THREATMODEL.md`, `lab/REPORT.md` |
| 2026-07-04 | Date of prior-art verification and benchmark artifacts | `NORTHSTAR2.md`, `lab/REPORT.md`, `lab/THRESHOLDS.md` |
| python3, demo-1, confidence 80 in shell commands | Reproduction command literals | `README.md` CLI examples and `caliber/cli.py` |
| URL numbers and classic years | External citation identifiers and allowed classic references | `NORTHSTAR2.md` section 5 |

## References

External citations are limited to the source set in `NORTHSTAR2.md` section 5:

- Fatebook: https://fatebook.io/
- Fatebook introduction: https://www.lesswrong.com/posts/yS3d46m23wRKDQobt/introducing-fatebook-the-fastest-way-to-make-and-track
- PredictionBook: https://www.lesswrong.com/posts/ofSYgmMby7iqxJqi6/predictionbook-com-track-your-calibration
- Agentic Confidence Calibration: https://arxiv.org/pdf/2601.15778
- TrustBench: https://arxiv.org/pdf/2603.09157
- BayesTruth: https://github.com/davccavalcante/bayestruth
- `mcp-confidence`: https://github.com/shaxzodbek-uzb/mcp-confidence
- Calibeating: https://arxiv.org/pdf/2209.04892
- Forecast hedging: https://simons.berkeley.edu/talks/forecast-hedging-calibration-game-equilibria
- Gneiting and Raftery, proper scoring rules: https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jrssb.pdf

Classical estimator citations used by name only here are the classics allowed
by `NORTHSTAR2.md` section 5: Brier 1950, Murphy 1973, Wilson 1927, and
Spiegelhalter 1986.
