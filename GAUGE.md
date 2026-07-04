# GAUGE — caliber

> Trust protocol for AI agents. Tracks predictions, measures calibration.
> Updated before every commit. Single source of truth.

**Current version**: v0.2.0 (on PyPI as `caliber-trust` — gaming detection release)
**Last session**: 2026-07-04 — northstar Phase 2 adversarial lab completed; Phase 3 tamper evidence is next
**Repo**: `northstar` branch, local only. Do not push. Do not publish. Baseline verified with 143 tests passing; current dev suite 179 tests passing.

---

## NEXT SESSION — START HERE

### Active northstar run (2026-07-04)

Read `NORTHSTAR.md` first. It supersedes the older "external user first" and
"don't rewrite storage" guidance for this branch. Current branch: `northstar`.
Branch rules: never push, never publish to PyPI, keep runtime dependencies
stdlib-only, and update `lab/NOTEBOOK.md` plus this file at phase gates.

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

Next concrete work: Phase 3 Tamper Evidence. Start with the append-only JSONL
event log design and compatibility tests before changing storage behavior.

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
