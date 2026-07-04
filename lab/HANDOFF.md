# Caliber Northstar Handoff - Phase 4 Gate

Date: 2026-07-04
Branch: `northstar`
Status: Phase 4 complete locally. Do not push. Do not publish to PyPI.

## Explanation To Me

Caliber is now a much more honest measurement tool for AI-agent calibration.
Earlier versions could make a few predictions look more meaningful than they
were, and the old commitment wording implied more proof than a local mutable
file can provide. The northstar work corrected the statistics, tested gaming
detectors against simulated attackers, added tamper-evident event logs, and
rewrote the public docs so they say exactly what the code can demonstrate.

Important terms:

- Calibration: whether 80% confidence is actually right about 80% of the time.
- Wilson interval: an uncertainty range around an observed accuracy.
- Exact binomial test: a small-sample-safe significance test for bucket
  accuracy.
- Murphy decomposition: a way to split Brier score into calibration,
  discrimination, and outcome uncertainty.
- Hash chain: each event stores the hash of the previous event, so editing,
  deleting, or reordering old history breaks verification.
- Anchor: a saved chain head. Once someone stores it outside the mutable local
  file, later rewrites can be detected from that point forward.

## Current State

- Local package version is `0.3.0`.
- PyPI still has v0.2.0 until Satish releases.
- Full suite evidence at the Phase 4 gate: `202 passed`.
- Northstar baseline was `143 passed`; new coverage added statistical tests,
  lab regressions, event-log verification, migration, and card verification.
- `docs/` is still untracked and was intentionally left alone.

## Engram-Worthy Learnings And Decisions

- DEC: Confidence bucket gaps now use mean stated confidence, not bucket
  midpoint. This is the D2 definition change and it changes reported numbers.
- DEC: Danger and strength zones require a completed significant test.
  Insufficient data can never create a zone by itself.
- LRN: NORTHSTAR's proposed Wilson Monte Carlo acceptance band was false for
  some small-n/extreme-p grid cells. Exact enumeration is the authority; the
  tests now pin real coverage instead of forcing a fake pass.
- LRN: Per-flag false-positive budgets do not imply a combined `any_flag`
  budget. Keep integrity output as separate advisory flags, never an aggregate
  score.
- LRN: Patient farming beats a latency-only detector but not distributional
  signals. Low outcome variance plus confidence/domain concentration catches
  it without `INSTANT_VERIFICATION`.
- BOUNDARY: Smart fabrication that samples outcomes from stated confidence is
  statistically indistinguishable from honest forecasting from the record
  alone. It needs witnessed timing, anchors, or external adjudication.
- BOUNDARY: Synthetic import timestamps are not fixable from mutable JSON
  records. Event origins plus hash-chain anchoring are the real defense.
- DEC: New stores use append-only event logs as source of truth; JSON remains a
  derived compatibility cache.
- DEC: Unanchored local commitments are self-attestation. Third-party tamper
  evidence starts only after a chain head is witnessed or anchored externally.
- MST: In a network-restricted fresh venv, `pip install -e .` can fail while
  trying to fetch isolated build dependencies. The local-checkout guide now
  documents `--system-site-packages` plus `--no-build-isolation`, and
  `pyproject.toml` uses PEP 621 table-form license metadata for older
  setuptools compatibility.

## Review Checklist For Satish

Read files in this order:

1. `CHANGELOG.md` - v0.3.0 release notes and the no-publish boundary.
2. `README.md` - public positioning, Trust Card excerpt, threat model, and
   roadmap wording.
3. `GETTING_STARTED.md` - first-user path and network-restricted local
   checkout note.
4. `caliber/card.py`, `tests/test_card.py`, `tests/test_card_properties.py` -
   statistical corrections and invariants.
5. `trust-card-claude-opus.json` - regenerated flagship card.
6. `lab/REPORT.md`, `lab/THRESHOLDS.md`, `lab/THREATMODEL.md` - adversarial
   evidence and record-only boundaries.
7. `caliber/integrity.py`, `tests/test_lab_bench.py`,
   `tests/test_integrity_adversarial.py` - measured threshold comments and
   regression expectations.
8. `caliber/event_log.py`, `caliber/storage.py`, `caliber/cli.py`,
   `tests/test_event_log.py`, `tests/test_storage.py`, `tests/test_cli.py` -
   event-log source of truth and verification commands.
9. `caliber/commitment.py` - commitment wording and evidence-level boundary.
10. `GAUGE.md` and `lab/NOTEBOOK.md` - phase evidence and command transcripts.

Commands to rerun:

```bash
git status -sb
git log --oneline -8
. /tmp/caliber-northstar-p1-properties/bin/activate
python3 -m pytest -q
rg -n "Trust protocol|trust protocol|Prove capability|prove capability|github.com/SatishoBananamoto/my-universe" README.md pyproject.toml caliber
python3 -m venv --system-site-packages /tmp/caliber-review-fresh
. /tmp/caliber-review-fresh/bin/activate
python3 -m pip install --no-build-isolation -e .
HOME=/tmp/caliber-review-home AGENT_NAME=review-smoke caliber -a "$AGENT_NAME" summary
```

The final smoke command should say there are no predictions yet, proving the
temp `HOME` boundary is being used.

## Decisions Needing Satish Sign-Off

- Accept the D2 definition change: bucket calibration gaps are now measured
  against mean stated confidence.
- Decide whether v0.3.0 should be published to PyPI from this local branch.
- Decide whether to push `northstar` as-is, squash, or merge through another
  review path.
- Decide whether the network-restricted local-checkout instructions belong in
  the public first-user guide or should move to a contributor/dev note.
- Decide whether Phase 5 `docs/METHOD.md` is required before release.

## Ranked Remaining Gaps

1. No external release action has happened. The branch is local only; PyPI
   remains v0.2.0.
2. External anchoring is manual. `caliber anchor` prints/appends a head, but
   Caliber does not publish it to a timestamping service or registry.
3. Record-only analysis cannot detect smart fabrication or prove semantic
   task difficulty. This requires witnessed timing and external adjudication.
4. Migrated legacy history is explicitly unwitnessed. The new chain proves
   future ordering, not the original timing of old JSON records.
5. External user validation is still open. No stranger has used Caliber and
   returned feedback.
6. Phase 5 `docs/METHOD.md` was not attempted in this run.
7. The exact system `python3 -m pytest -q` fails on this machine unless a dev
   environment with `hypothesis` is active. `hypothesis` is already a declared
   dev dependency, not a runtime dependency.

## Release Boundary

This handoff is a local release-candidate handoff, not a release. There was no
`git push`, no tag, no PyPI upload, no `master` checkout, and no runtime
dependency added.

## Round Two Phase A Handoff - 2026-07-04

Branch: `northstar2`
Status: Phase A complete in the work tree. Supervisor will create commits.
Phase B remains BLOCKED because `grep -n "R1-SIGNOFF" GAUGE.md` has no match.

### Explanation To Me

Round two made Caliber easier for an outsider to inspect. `docs/METHOD.md`
explains the method, the benchmark, and the limits. `docs/SPEC.md` describes
the exact record and verification format. The new vector files are small
examples that another implementation can use to check whether it computes the
same log hashes and the same card.

Important terms:

- Method paper: a written explanation of what Caliber measures and why.
- Spec: a precise rulebook for records, logs, cards, and verification.
- Golden vector: a fixed test example with an expected answer.
- Head hash: the SHA-256 hash at the end of the event-log chain.
- Standalone proof: a script that recomputes the hash without importing
  Caliber's own code.

### What Shipped

- A1: `docs/METHOD.md`, including problem statement, related work, estimator
  choices, adversarial benchmark tables, threat model, limitations,
  reproduction commands, references, and numeric source map.
- A2: `docs/SPEC.md` with `spec_version: 0.1`; `tests/vectors/` with valid
  log, tampered log, manifest, card JSON, and card-producing store; and
  `tests/test_spec_vectors.py`.
- A3: permitted leftovers only: CLAUDE identity wording, one AGENTS pointer
  line, and two README doc links.

### METHOD.md Claims Audit

- Numeric grep found 93 numeric lines in `docs/METHOD.md`.
- The document's "Numeric Claim Source Map" covers benchmark numbers,
  thresholds, estimator constants, formula terms, command literals, URL
  identifiers, and illustrative examples.
- Citation grep found only the `NORTHSTAR2.md` section 5 source set plus the
  explicitly allowed estimator classics.

### SPEC Version State

- Current spec version is `0.1`.
- Current Trust Card version remains `"0.1"`.
- Current event-log entry version remains `1`.
- Vector-validating test evidence: `tests/test_spec_vectors.py` -> 3 passed.
- Standalone stdlib proof recomputed valid vector head
  `ab5f201068385c1644d4ba62b37977ea7201009100c902e70610641de67ac442`.

### Engram-Worthy Learnings

- LRN: The spec must state that `verify-log` hashes raw stored line bytes, not
  a reserialized JSON object. That is necessary for third-party
  implementations to match Caliber's head hashes.
- LRN: Last-line edits change the unanchored head but do not fail structural
  verification unless an expected head is supplied. Specs and method wording
  must keep that boundary explicit.
- MST: During A3, the edits stayed inside the allowlist, but the notebook
  mini-plan was appended immediately after instead of before the tiny edits.
  Future sessions should add the notebook mini-plan before even small
  directive-listed cleanups.

### Decisions Needing Satish

- Review whether `docs/METHOD.md` should make the "first tool in the empty
  cell" claim as written, or soften it further before publication.
- Decide whether `docs/SPEC.md` v0.1 should be treated as public protocol
  language before a second implementation exists.
- Add `R1-SIGNOFF` to `GAUGE.md` only if round-one review is accepted; until
  then Phase B must stay blocked.

### Remaining Gaps, Re-ranked

1. Phase B is blocked pending explicit `R1-SIGNOFF`.
2. No signed cards or external adjudication yet; self-adjudication remains the
   largest trust boundary.
3. `docs/SPEC.md` has one implementation and executable vectors, but no second
   implementation has used it yet.
4. Anchoring remains manual; no timestamping service or registry publish path
   exists.
5. External user validation is still open.
6. No push, tag, PyPI publish, or `master` action happened in this run.
