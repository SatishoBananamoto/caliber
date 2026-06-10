# GAUGE — caliber

> Trust protocol for AI agents. Tracks predictions, measures calibration.
> Updated before every commit. Single source of truth.

**Current version**: v0.1.0 (on PyPI as `caliber-trust`; gaming detection not yet published)
**Last session**: 2026-06-10 — gaming-signature detection (integrity module, CLI, MCP, card embedding)
**Repo**: Main branch. Last verified locally with 131 tests passing.

---

## NEXT SESSION — START HERE

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

---

### Key reference files

| File | What it contains |
|------|-----------------|
| GAUGE.md | This file. |
| GETTING_STARTED.md | First-user tutorial and feedback prompt. |
| REVIEW.md | Structured assessment (grade A-). |
| CLAUDE.md | Detailed architecture + known issues + next steps. |
| INTEGRATIONS.md | How caliber connects to svx, engram, scroll, probe. |
