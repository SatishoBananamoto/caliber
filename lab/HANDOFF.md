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

## Round Two Phase B Handoff - 2026-07-05

Branch: `northstar2`
Status: Phase B complete in the work tree. Supervisor will create commits.
No push, no publish, no `master` action, and no git write commands were run by
the coding agent.

### Explanation To Me

Phase B made Trust Cards harder to fake and easier for outsiders to check.
Cards can now be signed with an optional Ed25519 key so the card is bound to a
specific event-log head. Caliber can also record an outside adjudicator's
judgment separately from the agent grading itself, and mixed cards no longer
hide those two sources behind one blended accuracy number. Anchors can now be
written to a separate file that can be committed to git as a public witness.

Important terms:

- Ed25519: a modern public-key signature algorithm.
- Optional extra: a dependency installed only by users who ask for it, here
  `caliber-trust[signing]`.
- Adjudication: an external person or system records whether a prediction was
  correct.
- Wilson interval: an uncertainty range around an observed accuracy.
- Anchor emit file: a separate JSONL file containing log heads that can be
  committed or published outside the mutable local store.

### What Shipped

- B1: optional signed cards:
  - `pyproject.toml` now has `[signing] = ["cryptography>=42.0"]`.
  - `caliber/signing.py` guards all `cryptography` imports.
  - New CLI: `caliber keygen`, `caliber card --sign`, and
    `caliber verify-card --pubkey <file>`.
  - Signatures cover canonical card JSON plus the current event-log head.
  - Unsigned cards and signed cards without `--pubkey` still verify ordinary
    calibration stats.
- B2: external adjudication:
  - New `adjudicated` event type.
  - New CLI: `caliber adjudicate <prediction-id> --correct/--incorrect --by
    <identity>`.
  - Prediction records preserve adjudicator identity, adjudication timestamp,
    evidence note, and optional adjudicator signature.
  - Cards expose `self_verified` and `adjudicated` sections with separate
    counts, accuracy, and Wilson intervals.
  - Mixed self/adjudicated cards omit `overall_accuracy` to avoid blending the
    two sources.
  - Integrity reports include `adjudicated_share` as a metric, not a flag.
  - `docs/SPEC.md` is now `spec_version: 0.2`.
  - Added adjudication golden vectors under `tests/vectors/adjudicated-store/`
    plus `tests/vectors/adjudicated-card.json`.
- B3: anchoring hardening:
  - `caliber anchor --emit <file>` appends the anchor result to a separate
    JSONL anchors file.
  - `GETTING_STARTED.md` documents the git-commit anchoring pattern.
  - `docs/SPEC.md` documents the emitted anchors-file fields.

### METHOD.md Claims Audit

No METHOD.md claims were changed in Phase B. Phase A's audit remains the
current METHOD evidence: 93 numeric lines covered by the source map, citation
set limited to NORTHSTAR2 section 5 plus allowed classics.

### SPEC Version State

- Current spec version is `0.2`.
- Current Trust Card version remains `"0.1"` with v0.2 optional fields.
- Current event-log entry version remains `1`.
- New supported event type: `adjudicated`.
- Vector-validating evidence:
  `/tmp/caliber-phaseb-venv/bin/python -m pytest tests/test_spec_vectors.py
  ... -q` was included in the focused B2 run -> `125 passed`.
- New adjudication vector head:
  `d16b1d7b9ae039c705da8ab40b163988334e74f47dea0eb9fce95bf4653c5517`.

### Verification

```text
$ /tmp/caliber-phaseb-venv/bin/python -m pytest -q
222 passed in 7.48s

$ PYTHONPATH=/tmp/caliber-no-cryptography /tmp/caliber-phaseb-venv/bin/python -m pytest -q
219 passed, 3 skipped in 6.21s
```

The exact requested phaseb venv was created. The direct install command failed
because pip build isolation attempted network access and the proxy returned
403. Verification used the repository's documented local fallback: make
already-installed local dev/signing packages visible to the venv, then install
Caliber editable with no network.

### Engram-Worthy Learnings

- DEC: Mixed self/adjudicated cards omit `overall_accuracy`; otherwise the
  field name invites a blended-accuracy reading even if the implementation used
  only self-verified data.
- DEC: `adjudicated_share` is a metric, not a flag. It reports evidence
  quality without turning third-party coverage into a suspiciousness threshold.
- DEC: Signed-card verification with `--pubkey` requires the signature's
  `event_log_head` to equal the current verified log head. A signed card binds
  to a specific log state.
- LRN: In this sandbox, the exact pip install command can fail due
  build-isolation network fetches even when all packages exist locally. Record
  the fallback clearly rather than treating it as a package failure.

### Decisions Needing Satish

- Decide whether Trust Card `trust_version` should bump from `"0.1"` to
  `"0.2"` now, or remain `"0.1"` while SPEC v0.2 defines optional fields.
- Review whether `overall_accuracy` omission on mixed cards is the desired
  public shape.
- Decide whether `caliber adjudicate` should also become an MCP tool in a
  later phase.
- Decide whether signed-card public keys should be named per agent as they are
  now, or whether project/team-level key identity is preferred.

### Remaining Gaps, Re-ranked

1. No release action has happened. The branch is local only; PyPI remains
   v0.2.0.
2. Signed cards depend on key custody outside Caliber. Key rotation,
   revocation, and identity discovery are not designed yet.
3. External adjudication exists structurally, but Caliber does not verify the
   adjudicator's optional signature or reputation.
4. Anchoring is still manual. `--emit` makes git/public witnessing easier, but
   there is no timestamping service or registry adapter.
5. Record-only analysis still cannot detect smart fabrication or semantic task
   difficulty without witnessed timing, anchoring, or meaningful external
   adjudication.
6. `docs/SPEC.md` has executable vectors but still no second implementation.
7. External user validation is still open.
8. Phase C is out of scope until a separate directive exists.
