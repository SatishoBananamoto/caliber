# GAUGE — caliber

> Calibration instrument for AI agents. Tracks predictions, measures calibration.
> Updated before every commit. Single source of truth.

**Current version**: v0.3.0 local northstar release candidate (v0.2.0 remains on PyPI as `caliber-trust`)
**Last session**: 2026-07-04 — northstar2 Phase A citable/specifiable docs completed in the work tree; Phase B blocked pending Satish's round-one signoff marker
**Repo**: `northstar2` branch, local only. Do not push. Do not publish. Baseline verified with 143 tests passing; current dev suite 205 tests passing.

---

## NEXT SESSION — START HERE

### External review response (2026-07-05)

An external review of `1a54be2` (ranges f6fa44d..e127398 and e127398..1a54be2)
found four issues; all are fixed on `northstar2`:

1. **P1 — spec/implementation non-equivalence.** `verify-log` accepted events
   that violated SPEC section 2's MUST table (wrong version, unknown type,
   empty event_id, wrong agent, bad datetime, non-object payload). Fix:
   `event_log.verify()` now enforces the full event-object table per line
   (SPEC 3.2 step 4 added); new golden vector `log-structural/`; the
   reviewer's six-probe set is a parametrized regression test. Independent
   spec-only verifier re-run: agrees with the implementation on all three
   vectors. Suite: 213 passing.
2. **P2 — stale "proves calibration" wording** removed from
   GETTING_STARTED.md, card.py, and integrity.py docstrings; repo-wide sweep
   for proof-language came back clean.
3. **P2 — AGENTS.md branch conflict** fixed: active-branch guidance now
   defers to GAUGE.md instead of hardcoding `northstar`.
4. **P3 — dirty worktree gate**: pre-existing untracked docs explainer
   artifacts are now gitignored.

### Active northstar run (2026-07-04)

Read `NORTHSTAR2.md` first, then the inherited constraints in `NORTHSTAR.md`.
Current branch: `northstar2`. Branch rules: never push, never publish to PyPI,
keep runtime dependencies stdlib-only, and update `lab/NOTEBOOK.md` plus this
file at phase gates.

Round Two Phase A is complete in the work tree:

- A1: `docs/METHOD.md` written as the citable method paper with numeric source
  map, benchmark tables, limitations, reproduction commands, and citations
  limited to `NORTHSTAR2.md` section 5.
- A2: `docs/SPEC.md` written as normative `spec_version: 0.1`; golden vectors
  added under `tests/vectors/`; `tests/test_spec_vectors.py` validates the
  vector head, tamper failure, and card-producing store.
- A3: only permitted leftovers changed: CLAUDE identity wording, one AGENTS
  pointer line, and two README doc links.
- Gate evidence: METHOD numeric grep found 93 numeric lines covered by the
  source map; standalone stdlib script recomputed vector head
  `ab5f201068385c1644d4ba62b37977ea7201009100c902e70610641de67ac442`;
  `python -m compileall -q caliber` exited 0; full suite reached 205 passing.
- Phase B remains BLOCKED: the exact round-one signoff marker is absent from
  this file.

Next concrete work: Satish review of round one and round two Phase A. If he
accepts round one, he can add the exact round-one signoff marker and Phase B
may start. Until that exact marker exists, do not start signed cards, external
adjudication, or anchoring hardening.

Phase 0 baseline is complete:

- deleted merged local branch `integrity-metrics`;
- created branch `northstar`;
- read `GAUGE.md`, `REVIEW.md`, all modules under `caliber/`, and
  `tests/test_integrity_adversarial.py`;
- ran `python3 -m pytest -q` -> 143 passed;
- recorded baseline `card` and `integrity` outputs for `default`, `test`, and
  `claude-trader` in `lab/NOTEBOOK.md`;
- observed drift: local `test` corpus has 88 verified predictions, and
  `trust-card-claude-opus.json` has 59 verified predictions plus the D1
  insufficient-data `strength_zones` bug.

Phase 1 statistical core is complete:

- D1: danger/strength zones now require a completed significant test;
  insufficient data cannot create a zone.
- D2: bucket calibration gaps now use mean stated confidence instead of bucket
  midpoint bias.
- D3/D4: bucket JSON and summaries carry Wilson intervals, and significance
  uses exact two-sided binomial p-values.
- Trust Cards now expose Brier score, Murphy decomposition, Spiegelhalter Z,
  and adaptive equal-mass buckets.
- Property/invariant tests live in `tests/test_card_properties.py`; fresh dev
  venv run: `161 passed`.
- `trust-card-claude-opus.json` and the README Trust Card excerpt were
  regenerated from the current MY UNIVERSE corpus: 94 verified predictions,
  no `strength_zones` small-sample claim remains.
- Important correction: NORTHSTAR's proposed "93-97% Wilson coverage on every
  small-n grid cell" was false by exact enumeration. The tests now pin the
  true coverage table and use Monte Carlo only as a smoke check.

Phase 2 adversarial lab is complete:

- Built deterministic simulators for 12 populations in `lab/simulate.py`.
- Built `lab/run_bench.py`; full bench artifact
  `lab/results/bench-08b2cff.json` has 48 rows (12 populations x sample sizes
  20, 50, 100, 300), 500 replicates per cell, and runtime under 5 minutes.
- Re-derived every integrity threshold at n=50 with measured clean FPR and
  target attacker power; `caliber/integrity.py` carries operating-point
  comments for each threshold.
- Added fast bench regression coverage in `tests/test_lab_bench.py`; current
  full suite is `179 passed`.
- Wrote `lab/THREATMODEL.md`: patient farmer is caught without latency;
  smart fabrication and synthetic import timestamps are explicit record-only
  limits; Phase 3 must add anchored event history.

Phase 3 tamper evidence is complete:

- Added append-only hash-chained JSONL event logs in `caliber/event_log.py`.
- New stores replay the event log as source of truth; JSON remains a derived
  cache, and legacy JSON-only stores stay compatible until explicit migration.
- Added `caliber verify-log`, `caliber anchor`, `caliber migrate`, and
  `caliber verify-card`.
- Migration marks old records as imported/migrated history rather than
  pretending they were witnessed.
- Real scratch-corpus migration round-trip passed for `default`, `test`, and
  `claude-trader`; verified-card/tamper tests are in the suite.
- README and `commitment.py` now state that unanchored commitments are
  self-attestation unless the chain head is witnessed or anchored externally.

Phase 4 honest repositioning is complete:

- README now identifies Caliber as a calibration instrument, not a trust
  protocol, and frames registries/A2A as motivation rather than current
  capability.
- README threat-model language distinguishes record-only evidence, event-log
  tamper evidence, anchored-head evidence, and external adjudication.
- `GETTING_STARTED.md` was walked end-to-end in a fresh temp-home flow; the
  transcript is in `lab/NOTEBOOK.md` under EXP-027.
- `CHANGELOG.md` now has a v0.3.0 entry that calls out statistical
  corrections, adversarial lab evidence, tamper-evidence commands, and the
  no-publish boundary.
- Local package metadata is bumped to `0.3.0`; Satish still owns all push and
  PyPI release decisions.
- `lab/HANDOFF.md` is the review starting point.

Next concrete work: Satish review and release decision. Start with
`lab/HANDOFF.md`, then review `CHANGELOG.md`, `README.md`,
`GETTING_STARTED.md`, the statistical/card changes, the lab evidence, and the
event-log verification path. Do not push or publish until Satish explicitly
decides to release.

### What just happened (2026-06-10)

Built Phase 2 gaming detection end to end: `caliber/integrity.py` (Murphy
decomposition + 7 advisory flags), `caliber integrity` CLI, `caliber_integrity`
MCP tool, `caliber card --with-integrity`. 131 tests pass. Real-data check
flagged the imported CALIBRATE corpus as UNWITNESSED_HISTORY and the live
`default` store as LOW_OUTCOME_VARIANCE + INSTANT_VERIFICATION — both correct
and informative. Not yet published to PyPI (still v0.1.0 there).

### Prior session (2026-05-11)

Added `GETTING_STARTED.md` for first external users: install, first three
predictions, verification, summary, Trust Card generation, import, MCP setup,
and concrete feedback prompts. 105 tests pass.

### Prior shipped baseline (2026-03-27)

Shipped v0.1.0 to PyPI. MCP server working (6 tools: predict, verify, card, summary, list, trajectory). Used during real vigil engineering work (5 predictions, 4/5 correct). Added Trust Card badge generator. REVIEW.md grade A-. 96 tests. CI green. Commitment scheme has 9 tests including tamper detection.

### #1 Priority: Get one external user

REVIEW.md identified: no external users. caliber has only been used by Satish's own agent. Stranger validation needed to prove the tool is useful beyond its creator. Post in Claude Code community or AI agent forums.

### What NOT to do

- Don't rewrite storage — file-based JSON is fine for current scale
- Don't build verification for Trust Cards yet — needs the commitment scheme tested more first
- Don't reduce integrity findings to a single score — a lone number is itself gameable; report flags with evidence

> 2026-06-10: removed "don't add difficulty metrics yet" — Satish directed
> work on the difficulty/gaming problem (D-003). The original deferral reason
> (needs usage data) is partly satisfied: ~94 verified predictions exist from
> the CALIBRATE corpus and real vigil field use.

---

## Work

### External adoption

_No strangers have used caliber. Need validation outside Satish's workflow._

- [x] Write a "getting started" tutorial or blog post — 2026-05-11 · `GETTING_STARTED.md`
- [ ] Post in Claude Code community / AI agent forums
- [ ] Collect feedback from first external user
- [ ] Adjust based on feedback

### Integration hardening

_MCP server works but integration points need polish._

- [x] MCP config auto-apply — 2026-05-11 · `caliber mcp-config --install` merges the server entry with backup coverage
- [x] Test multi-agent workflows (two agents with different Trust Cards) — 2026-05-11 · CLI regression covers shared-store separation and collision-prone agent names
- [x] Add `caliber trajectory` CLI command — verified 2026-05-10 · `tests/test_cli.py`
- [x] Clean up extract_calibrate_md.py (standalone script → use `caliber import` command) — 2026-05-11 · wrapper now reuses shared importer; CLI import has regression coverage

### Phase 2: Trust Card integrity (ACTIVE as of 2026-06-10)

_Unlocked by Satish's direction. Approach: gaming detection via deterministic
statistics on the prediction stream — no LLM judge. Core: Murphy decomposition
of the Brier score (reliability/resolution/uncertainty). A trivial-prediction
farmer shows near-zero uncertainty (outcome base rate ≈ 1.0) and near-zero
resolution — calibration is gameable, discrimination is not. Supporting
signals: confidence concentration, domain concentration (Herfindahl), duplicate
claims, predict→verify latency (LRN-041: instant verification ≈ post-hoc
prediction), batch-import share (unwitnessed history). Every signal gates on
minimum N (LRN-021/LRN-022). Output: advisory flags with evidence, never a
single score._

- [x] `caliber/integrity.py` — IntegrityReport with Murphy decomposition + farming signals — 2026-06-10 · 18 tests, real-data smoke test flagged the imported corpus as UNWITNESSED_HISTORY (correct)
- [x] CLI command `caliber integrity` — 2026-06-10 · text + `--json`, 3 CLI regressions; suite 126 passing
- [x] MCP tool `caliber_integrity` — 2026-06-10 · 7th server tool; test proves in-session farming via MCP gets caught (incl. INSTANT_VERIFICATION); suite 129 passing
- [x] Embed integrity section in Trust Card output (opt-in) — 2026-06-10 · `caliber card --with-integrity` attaches the report to the shared artifact; default output unchanged; suite 131 passing
- [x] Red-team the detector + Mendel test — 2026-06-10 · `tests/test_integrity_adversarial.py` encodes evasion strategies; SUSPICIOUSLY_PERFECT catches the calibrated forger (outcomes fabricated to match confidence — evades all behavioral flags, fails lower-tail chi-square); real CALIBRATE corpus p_low=0.66, no false positive; suite 142 passing
- [x] Template-claim detection — 2026-06-10 · `template_claim_ratio` metric (digit-normalized Jaccard clustering). Deliberately a METRIC not a flag: honest bulk workloads (vigil-style scans) are equally templated — template form can't distinguish farming from honest repetitive work, outcome variance does. Red-team test fixture proved the point: my first "honest bulk user" fixture was correctly flagged NO_DISCRIMINATION because its confidence carried no information. Suite 143 passing.
- [ ] Trust Card verification — chi-square on distributions, consistency checks
- [ ] A2A Agent Card extension — add calibration data to Agent Cards

### Done

<details>
<summary>v0.1.0 — completed 2026-03-27</summary>

- [x] Core library: TrustTracker, Prediction, TrustCard — `commit:476c6e4`
- [x] CLI: predict, verify, card, summary, list, import, trajectory — click-based
- [x] MCP server: 6 tools via FastMCP — `engram:DEC-002`
- [x] Commitment scheme: SHA-256 prediction anchoring — `commit:db6d8d7`
- [x] Importer: CALIBRATE.md format from MY UNIVERSE — `commit:bc91aa5`
- [x] Integration designs: svx, engram, scroll, probe — `commit:db6d8d7`
- [x] Ship to PyPI as caliber-trust — `commit:8d1cb7e`
- [x] REVIEW.md: A- grade — `commit:6f6da41`
- [x] Badge generator — `commit:f5dfb2f`
- [x] Tamper tests for commitment scheme — `commit:4593e14`
- [x] CI — `commit:fdf9ee8`
- [x] CLI trajectory regression tests — 2026-05-10 · 98 tests passing
- [x] CLI multi-agent workflow regression tests — 2026-05-11 · 101 tests passing
- [x] CALIBRATE import wrapper cleanup — 2026-05-11 · 103 tests passing
- [x] MCP config installer helper — 2026-05-11 · 105 tests passing
- [x] First-user getting-started tutorial — 2026-05-11 · `GETTING_STARTED.md`

</details>

---

## Decision Log

| ID | Date | Decision | Why |
|----|------|----------|-----|
| D-001 | 2026-03-26 | Published as caliber-trust (not caliber) | Name taken by existing ML library. |
| D-002 | 2026-03-26 | SHA-256 commitment scheme for prediction anchoring | Cryptographic proof of timing without external services. Standard, simple. |
| D-003 | 2026-06-10 | Gaming detection = behavioral statistics, not claim NLP | Claim-text "specificity scoring" is itself gameable and language-dependent. Distributional signals (Brier resolution, outcome variance, latency, concentration) can't be faked without taking real predictive risk. Advisory flags with evidence, never one aggregate score. |

---

## Session Log

### 2026-07-04 — Northstar2 Phase A citable/specifiable docs (Codex/Kai)

- **Worked on:** `NORTHSTAR2.md` Phase A only: method paper, normative spec,
  golden vectors, three permitted leftover edits, gate tracking, and handoff.
- **Completed:** `docs/METHOD.md`; `docs/SPEC.md`; `tests/vectors/`;
  `tests/test_spec_vectors.py`; CLAUDE identity wording; AGENTS pointer line;
  README METHOD/SPEC links; Round Two handoff section.
- **Claims audit:** `docs/METHOD.md` numeric grep found 93 numeric lines, all
  covered by the document's numeric source map. Citation grep stayed within
  `NORTHSTAR2.md` section 5 plus the allowed estimator classics.
- **Spec proof:** `tests/test_spec_vectors.py` passed with 3 tests; a
  standalone stdlib script, importing nothing from `caliber/`, recomputed
  valid vector head
  `ab5f201068385c1644d4ba62b37977ea7201009100c902e70610641de67ac442`.
- **Evidence:** A1 full suite -> 202 passed; A2 vector test -> 3 passed; A2
  full suite -> 205 passed; A3 full suite -> 205 passed; compileall clean.
- **Skipped/blocked:** Phase B and Phase C not started because Satish's
  round-one signoff marker is absent. No push, no PyPI publish, no git write
  command, no runtime dependency added, and no integrity threshold changed.
- **State:** Work tree contains Phase A deliverables for supervisor commit.

### 2026-07-04 — Northstar Phase 4 honest repositioning (Codex/Kai)

- **Worked on:** Phase 4 from `NORTHSTAR.md`: honest public positioning,
  fresh-venv getting-started verification, v0.3.0 changelog/version bump,
  phase-gate tracker update, and handoff.
- **Completed:** README identity rewrite away from "trust protocol";
  evidence-level threat model in README; clean temp-home
  `GETTING_STARTED.md` walkthrough transcript; network-restricted local
  checkout install note; `CHANGELOG.md`; local version bump to `0.3.0`;
  `lab/HANDOFF.md`.
- **Headline numbers:** test suite grew from the northstar baseline `143
  passed` to `202 passed`; flagship card regenerated from 94 verified
  predictions with 75.5% accuracy, 70.7% mean confidence, mean calibration gap
  `-0.048`, Brier `0.1798`, and no `danger_zones` or `strength_zones`; the
  90-99 bucket's apparent `0.425` gap remains `insufficient_data` at n=2.
- **Bench summary:** full Phase 2 bench covers 12 populations x 4 sample
  sizes with 500 seeded replicates per cell. At n=50, `honest` any-flag rate
  was 2.8%; at n=100, 1.0%. Farmer, patient farmer, naive fabricator,
  template spammer, duplicate spammer, domain camper, and bulk importer all
  hit 100% detection at n=50 and n=100. Smart fabrication remains the
  record-only boundary (4.6% any-flag at n=50, 1.4% at n=100).
- **Evidence:** Phase 4 claim grep found no old "trust protocol" / private
  `my-universe` / fabricated-card overclaim matches; temp-home walkthrough
  created only `getting-started-smoke.events.jsonl`,
  `getting-started-smoke.json`, and a temp MCP config; final full suite
  `/tmp/caliber-northstar-p1-properties/bin/python3 -m pytest -q` ->
  202 passed.
- **Skipped/blocked:** Phase 5 `docs/METHOD.md` was not attempted. No push,
  no PyPI publish, no `master` touch. Remaining gaps are ranked in
  `lab/HANDOFF.md`.
- **State:** Phase 4 gate accepted locally on `northstar`. Next: Satish review
  and release decision.

### 2026-07-04 — Northstar Phase 3 tamper evidence (Codex/Kai)

- **Worked on:** Phase 3 from `NORTHSTAR.md`: event logs, chain verification,
  anchoring, migration, card verification, and commitment/README honesty.
- **Completed:** `caliber/event_log.py`; event-log-backed `FileStorage`;
  `caliber verify-log`; `caliber anchor`; `caliber migrate`;
  `caliber verify-card`; migration/card/tamper tests; real scratch-corpus
  migration round-trip; README and commitment evidence-level wording.
- **Evidence:** real `/tmp/codex-caliber-p3-realcorpus` scratch migration kept
  `default` and `test` card statistics identical and round-tripped
  `claude-trader` prediction counts; `/tmp/caliber-northstar-p1-properties/bin/python -m pytest -q`
  -> 202 passed.
- **State:** Phase 3 gate accepted locally on `northstar`, not pushed. Next:
  Phase 4 honest repositioning: README claim cleanup, clean-venv
  `GETTING_STARTED.md` transcript, CHANGELOG v0.3.0, version bump only after
  docs are honest. Do not publish.

### 2026-07-04 — Northstar Phase 2 adversarial lab (Codex/Kai)

- **Worked on:** Phase 2 from `NORTHSTAR.md`: simulator zoo, full FPR/power
  bench, threshold re-derivation, fast regression tests, and threat model.
- **Completed:** `lab/simulate.py`, `lab/run_bench.py`,
  `lab/analyze_thresholds.py`, `lab/REPORT.md`, `lab/THRESHOLDS.md`,
  `lab/THREATMODEL.md`, `tests/test_lab_bench.py`, and measured threshold
  comments in `caliber/integrity.py`.
- **Evidence:** `lab/results/bench-08b2cff.json` (48 rows, 500 replicates per
  cell); `lab/results/thresholds-c31299f.json` (8 threshold analyses);
  `/tmp/caliber-northstar-p1-properties/bin/python -m pytest -q` ->
  179 passed.
- **State:** Phase 2 gate accepted locally on `northstar`, not pushed. Next:
  Phase 3 tamper evidence: append-only hash-chained event log, `verify-log`,
  `anchor`, `verify-card`, and migration/compatibility proof.

### 2026-07-04 — Northstar Phase 1 statistical core (Codex/Kai)

- **Worked on:** Phase 1 from `NORTHSTAR.md`: statistical rigor for Trust
  Cards, property tests, and flagship-card correction.
- **Completed:** D1-D4 fixes; mean-confidence bucket gaps; Wilson intervals;
  exact binomial significance; Brier/Murphy fields; Spiegelhalter Z; adaptive
  buckets; Hypothesis-backed invariant tests; regenerated
  `trust-card-claude-opus.json`; README card excerpt and interpretation.
- **Evidence:** disposable dev venv full suite
  `/tmp/caliber-northstar-p1-properties/bin/python -m pytest -q` ->
  161 passed. Notebook records real-corpus checks and the Wilson coverage
  correction.
- **State:** Phase 1 gate accepted locally on `northstar`, not pushed. Next:
  Phase 2 Adversarial Lab (`lab/simulate.py`, `lab/run_bench.py`,
  `lab/REPORT.md`, threshold operating points, `lab/THREATMODEL.md`).

### 2026-03-26 — Core build (Session 1)

- **Worked on:** Extracted caliber from MY UNIVERSE calibration practice
- **Completed:** Core library, CLI, MCP server, importer, commitment scheme
- **State:** Working, not yet published

### 2026-03-27 — Ship + harden (Session 2)

- **Worked on:** PyPI, integrations, badge, REVIEW, CI
- **Completed:** v0.1.0 on PyPI, 96 tests, CI green
- **Engram:** DEC-001 (name), DEC-002 (commitment scheme)
- **State:** Shipped. Next: external users.

### 2026-05-10 — Codex/Kai field session

- **Worked on:** Tracking drift around `caliber trajectory`
- **Completed:** Added CLI regression tests for `trajectory`; updated README, REVIEW, and GAUGE to reflect that trajectory support is already in v0.1
- **Why:** GAUGE/REVIEW still listed trajectory CLI as open even though `caliber/cli.py` and `caliber/mcp_server.py` already exposed it
- **State:** 98 tests passing. Next remains external user validation.

### 2026-05-11 — Codex/Kai field session

- **Worked on:** Multi-agent workflow hardening
- **Completed:** Added CLI regression for two agents sharing one store and generating separate Trust Cards; fixed URL-safe agent filenames with legacy load fallback
- **Why:** REVIEW and GAUGE still listed multi-agent workflows as untested, and the old storage sanitizer could collide for distinct agent names
- **State:** 101 tests passing. Next remains external user validation.

### 2026-05-11 — Codex/Kai field session

- **Worked on:** CALIBRATE import cleanup
- **Completed:** Archived the previous standalone parser, converted `extract_calibrate_md.py` into a compatibility wrapper around the shared importer, and added CLI import coverage
- **Why:** GAUGE still listed the standalone script cleanup as open, and duplicate parser logic could drift from the maintained import path
- **State:** 103 tests passing. Next remains external user validation.

### 2026-05-11 — Codex/Kai field session

- **Worked on:** MCP config friction
- **Completed:** Added `caliber mcp-config` with print and `--install` modes; install preserves existing servers and writes a timestamped backup before updating an existing config
- **Why:** GAUGE still listed MCP config auto-apply as open, but touching the real `~/.mcp.json` directly would be the wrong trust boundary
- **State:** 105 tests passing. Next remains external user validation.

### 2026-05-11 — Codex/Kai field session

- **Worked on:** External adoption prep
- **Completed:** Added `GETTING_STARTED.md` and linked it from README
- **Why:** GAUGE's #1 priority is external validation; the non-account-bound next step was a concrete first-user walkthrough before any community post
- **State:** 105 tests passing. Next requires Satish or an external user to actually post/use it and return feedback.

### 2026-06-10 — Integrity / gaming detection (Fable session, branch `integrity-metrics`)

- **Worked on:** Phase 2 unlock — trivial-prediction-farming detection
- **Completed:** `caliber/integrity.py` (IntegrityReport: Murphy decomposition
  of Brier score + 7 advisory flags with evidence and min-N gates) and
  `tests/test_integrity.py` (18 tests). Full suite 123 passing.
- **Why:** Satish directed work on the difficulty/gaming problem (D-003).
  Calibration is gameable; resolution and outcome variance are not.
- **Real-data check:** imported CALIBRATE corpus correctly flagged
  UNWITNESSED_HISTORY; live `default` store flagged LOW_OUTCOME_VARIANCE +
  INSTANT_VERIFICATION (the LRN-041 signature in the field).
- **State:** Complete and merged to master. Commits 96e6795 (module),
  03d0205 (CLI), d9cac12 (MCP), ef14c20 (card embedding), d1bab8c (docs).
  131 tests passing. Next: bump version + publish to PyPI when Satish says
  go; remaining Phase 2 items are card verification and A2A extension.

### 2026-06-10 — Red-team iteration (Fable session, direct on master)

- **Worked on:** Adversarial probing of the new detector — gaming strategies
  as test cases (`tests/test_integrity_adversarial.py`).
- **Completed:** Mendel test (SUSPICIOUSLY_PERFECT: lower-tail chi-square via
  Wilson–Hilferty catches outcomes fabricated to match confidence — the one
  strategy that evades all behavioral flags); `template_claim_ratio` metric
  (deliberately not a flag — honest bulk workloads are equally templated).
  Residual gaps documented as tests: patient farmer beats any fixed latency
  window; synthetic import timestamps beat the equality heuristic (only the
  commitment scheme closes that). Commits 100752c, b3527ba. 143 tests passing.
- **False-positive checks:** real CALIBRATE corpus mendel_p_low=0.66 (clean);
  real claims template ratio 0.0. My first "honest bulk user" fixture was
  correctly flagged NO_DISCRIMINATION — its confidence carried no information;
  the detector outed my own bad test data.
- **Docs follow-up:** f1ee24a (README Mendel + metric-vs-flag policy),
  b391a19 (INTEGRATIONS.md integrity notes incl. svx instant-verify
  exemption constraint; GETTING_STARTED.md integrity step).
- **State:** Detector hardened against the strongest known evasion; docs
  current.

### 2026-06-10 — v0.2.0 release (Satish + Fable)

- **Shipped:** v0.2.0 published to PyPI (verified live: wheel + sdist),
  all commits + `v0.2.0` tag pushed to GitHub. Old 0.1.0 dists archived
  to `archive/dist-0.1.0/`.
- **Process note:** kv-secrets v0.4.0 grant scoping is cwd-sensitive — a
  grant approved from `~` did not match the same command run from
  `~/caliber`. Re-approving from the project directory fixed it. Possible
  UX finding for kv-secrets (error message doesn't say which scope field
  mismatched).
- **State:** Released. Next: community post (draft ready, posts under
  Satish's account) → first external user. Card verification stays locked.

---

### Key reference files

| File | What it contains |
|------|-----------------|
| GAUGE.md | This file. |
| GETTING_STARTED.md | First-user tutorial and feedback prompt. |
| REVIEW.md | Structured assessment (grade A-). |
| CLAUDE.md | Detailed architecture + known issues + next steps. |
| INTEGRATIONS.md | How caliber connects to svx, engram, scroll, probe. |
