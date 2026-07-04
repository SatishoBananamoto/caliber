# Caliber Threat Model - Phase 2 Adversarial Lab

Generated during the `northstar` branch Phase 2 work. This file describes what
Caliber's current record-only integrity analysis can and cannot detect.

Evidence sources:

- Full bench: `lab/results/bench-08b2cff.json`, rendered in `lab/REPORT.md`
- Threshold analysis: `lab/results/thresholds-c31299f.json`, rendered in
  `lab/THRESHOLDS.md`
- Fast regression: `tests/test_lab_bench.py`
- Residual evasion tests: `tests/test_integrity_adversarial.py`

## Scope

Caliber currently analyzes a stored prediction record: claims, confidences,
domains, outcomes, prediction timestamps, verification timestamps, and whether
records look imported. It does not witness the prediction being made, does not
anchor history externally, and does not know the semantic difficulty of a
claim.

Current integrity flags are advisory. They identify suspicious record shapes.
They do not prove fraud, intent, or bad faith.

## Evidence Levels

| level | evidence | what it can support |
| --- | --- | --- |
| Record only | Existing JSON prediction records | Calibration statistics and distributional gaming signatures. |
| Witnessed timing | Prediction events observed before outcomes are known | Stronger defense against backfilled predictions and fake latency. |
| Anchored history | Append-only hash chain with external chain-head anchors | Third parties can detect retroactive rewrites after an anchor. |
| External adjudication | Independent ground-truth checks or task witnesses | Harder semantic questions: task difficulty, claim quality, and whether outcomes were honestly judged. |

Phase 2 improves the first level only. Phase 3 must add anchored history.

## Detected Attacks

Rates below are from `bench-08b2cff`, 500 deterministic replicates per cell.
The n=50 threshold analysis kept every measured threshold's clean per-flag FPR
at or below 5%.

| attack | main signal | n=50 detection | n=100 detection | interpretation |
| --- | --- | ---: | ---: | --- |
| farmer | LOW_OUTCOME_VARIANCE, CONFIDENCE_CONCENTRATION, DOMAIN_CONCENTRATION, INSTANT_VERIFICATION | 100.0% | 100.0% | Easy, high-confidence, quickly verified claims are caught by multiple independent signals. |
| patient_farmer | LOW_OUTCOME_VARIANCE, CONFIDENCE_CONCENTRATION, DOMAIN_CONCENTRATION | 100.0% | 100.0% | Waiting out the latency window does not evade the distributional signals. |
| naive_fabricator | NO_DISCRIMINATION, SUSPICIOUSLY_PERFECT | 100.0% | 100.0% | Outcomes that are shaped too perfectly around confidence are caught. |
| template_spammer | NO_DISCRIMINATION | 100.0% | 100.0% | Template form alone is not a flag, but low discrimination catches this simulated spammer. |
| duplicate_spammer | DUPLICATE_CLAIMS | 100.0% | 100.0% | Repeated normalized claims are directly visible. |
| domain_camper | DOMAIN_CONCENTRATION | 100.0% | 100.0% | Narrow-domain activity is directly visible. |
| bulk_importer | UNWITNESSED_HISTORY | 100.0% | 100.0% | Timestamp-equal imports are visible as unwitnessed history. |

Patient farmer closes one original D8 gap: latency alone is beatable, but the
same stream still has low outcome variance plus confidence and domain
concentration. The fast regression test requires this explicitly: patient
farmer must be caught while `INSTANT_VERIFICATION` stays quiet.

Template ratio remains a metric, not a flag. Honest bulk work can be templated
too, so Caliber only flags when the record also shows low discrimination or
another suspicious statistical shape.

## Clean And Boundary Populations

Bench populations are not all "good users"; they are probes. The lab separates
three categories:

- `honest`: calibrated Bernoulli outcomes with varied claims/domains.
- `overconfident`, `underconfident`, `noisy`: biased or lower-quality
  forecasters, not necessarily attackers.
- `smart_fabricator`: a boundary case that generates statistically plausible
  Bernoulli outcomes from stated confidence.

At n=100 in the full bench, these populations stayed near the expected false
positive budget:

| population | any flag at n=100 |
| --- | ---: |
| honest | 1.0% |
| overconfident | 1.4% |
| underconfident | 1.4% |
| noisy | 1.0% |
| smart_fabricator | 1.4% |

At n=50, `overconfident` had a 7.2% any-flag rate even though each underlying
flag remained under the per-flag threshold budget. This matters: combined
`any_flag` rates can exceed a per-flag 5% budget. Caliber should present flags
individually, not collapse them into a single integrity score.

At n=20, low outcome variance is noisy. `honest@n=20` fired 18.4%. Small sample
Trust Cards should treat integrity flags as weak screening signals, not final
judgments.

## Record-Only Limits

### Smart Fabrication

A smart fabricator can generate distinct claims, ordinary domains, ordinary
latencies, and outcomes sampled from `Bernoulli(confidence)`. That record is
statistically indistinguishable from an honest forecaster by construction.

Measured evidence: `smart_fabricator@n=50` had 4.6% any-flag rate and
`smart_fabricator@n=100` had 1.4%, similar to clean populations.

This is not a detector bug. It is an information boundary. A record-only
detector cannot tell whether statistically plausible outcomes were witnessed in
real time or fabricated later.

Required fix: witnessed prediction events plus anchored history. Once the
prediction existed before the outcome and the history head was anchored, a
third party can detect retroactive replacement from that anchor forward.

### Synthetic Import Timestamps

The current `UNWITNESSED_HISTORY` heuristic treats `timestamp == verified_at`
as imported/backfilled history. An attacker who writes a JSON store can invent
plausible non-equal `verified_at` offsets, making `import_share == 0.0`.

The residual test `test_synthetic_import_timestamps_evade_import_share`
documents this gap. It is not fixable from mutable JSON records alone.

Required fix: the Phase 3 event log must record event origin (`predicted`,
`verified`, `imported`) and chain each event with `prev_hash`. External anchors
then make later rewrites detectable.

### Semantic Difficulty And Claim Quality

Caliber can see distributions, not meaning. It cannot prove that a claim was
valuable, hard, independently adjudicated, or non-trivial from text alone.
Claim-text judging would be gameable and language-dependent.

Required fix: external adjudication, task witnesses, or domain-specific review
outside the record-only detector.

## Current Design Consequences

- Keep integrity output as separate flags with evidence. A single aggregate
  score would hide the difference between sample-size noise, biased but honest
  forecasting, and adversarial record shapes.
- Do not turn template ratio into a flag without additional evidence; honest
  repetitive workflows can look templated.
- Treat n<50 distributional flags as weak signals unless corroborated by direct
  behavioral evidence.
- Document that unanchored commitments and mutable JSON stores are
  self-attestation only. Third-party tamper evidence starts with anchored event
  history, not with a pretty card.

## Phase 3 Requirements Implied By This Model

Phase 3 should add:

1. Append-only JSONL events with `prev_hash`.
2. Explicit event origins: `predicted`, `verified`, and `imported`.
3. `caliber verify-log` to detect edited, deleted, or reordered history.
4. `caliber anchor` to print and append the current chain head for external
   anchoring.
5. `caliber verify-card <card.json>` to recompute card statistics from the
   event log and fail on mismatch.

Without those pieces, Caliber measures calibration and flags suspicious record
shapes, but it does not prove that the record existed before the outcomes.
