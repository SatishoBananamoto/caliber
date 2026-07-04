# Changelog

## v0.3.0 - 2026-07-04

Northstar release candidate. Local branch only until Satish publishes it.

### Statistical corrections

- Corrected confidence-zone gating: danger and strength zones now require a
  completed significant test. Small buckets marked `insufficient_data` cannot
  create zones by themselves.
- Corrected bucket calibration gaps to compare observed accuracy with the
  bucket's mean stated confidence, not the fixed bucket midpoint. This can
  change existing Trust Card numbers.
- Added Wilson 95% confidence intervals to confidence buckets and adaptive
  buckets.
- Replaced the small-n normal approximation with an exact two-sided binomial
  test.
- Added Brier score, Murphy decomposition fields, Spiegelhalter calibration Z,
  and adaptive equal-mass buckets to Trust Cards.
- Regenerated the flagship `trust-card-claude-opus.json` artifact from 94
  verified predictions. The previous small-sample strength-zone claim is gone.

### Adversarial lab

- Added deterministic simulators and benchmark tooling under `lab/` for honest
  and adversarial prediction streams.
- Measured integrity-flag false positive rates and detection power in
  `lab/REPORT.md`; the full bench uses 500 seeded replicates per population
  and sample size.
- Re-derived integrity thresholds from the bench. Threshold constants now carry
  measured operating-point comments.
- Added fast lab regression tests so expected attacker populations trip their
  target flags and clean populations stay within the false-positive budget.
- Documented record-only limits in `lab/THREATMODEL.md`, including smart
  fabrication, synthetic import timestamps, and semantic task difficulty.

### Tamper evidence

- Added append-only JSONL event logs with a SHA-256 hash chain.
- New stores replay the event log as source of truth while keeping JSON
  snapshots as derived caches for compatibility.
- Added `caliber verify-log` to detect edited, deleted, or reordered history.
- Added `caliber anchor` to append and print a chain-head anchor suitable for
  external witnessing.
- Added `caliber migrate` to convert legacy JSON stores into event logs marked
  as imported history.
- Added `caliber verify-card` to recompute Trust Card statistics from the
  event log and reject mismatches.
- Updated commitment wording: unanchored local commitments are
  self-attestation; third-party tamper evidence starts when a chain head is
  witnessed or anchored outside the mutable local store.

### Documentation and packaging

- Repositioned Caliber as a calibration instrument rather than a trust
  protocol.
- Added README threat-model language for record-only, event-log, anchored-head,
  and external-adjudication evidence levels.
- Verified `GETTING_STARTED.md` in a temp-home fresh venv flow and documented a
  network-restricted local-checkout install path.
- Changed package license metadata to the PEP 621 table form for older
  setuptools compatibility.

### Release note

- Version bumped to `0.3.0` in package metadata.
- Do not publish this release from automation. Satish owns PyPI release and
  push decisions.

## v0.2.0 - 2026-06-10

- Added Trust Card integrity analysis with advisory gaming-signature flags.
- Added `caliber integrity` and `caliber card --with-integrity`.
- Added MCP support for integrity reports.

## v0.1.0 - 2026-03-27

- Initial public release as `caliber-trust`.
- Added core prediction tracking, CLI, MCP server, importer, trajectory
  support, badge generation, and SHA-256 commitment hashes.
