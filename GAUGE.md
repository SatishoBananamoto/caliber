# GAUGE — caliber

> Trust protocol for AI agents. Tracks predictions, measures calibration.
> Updated before every commit. Single source of truth.

**Current version**: v0.1.0 (on PyPI as `caliber-trust`)
**Last session**: 2026-05-11 — tested multi-agent CLI workflows and fixed storage name collisions
**Repo**: Main branch. Last verified locally with 101 tests passing.

---

## NEXT SESSION — START HERE

### What just happened (2026-05-11)

Added a public CLI regression for two agents sharing one store and generating
separate Trust Cards. While testing that boundary, fixed `FileStorage` agent
filename collisions by URL-encoding agent names and retaining legacy load
fallback for older sanitized files. 101 tests pass.

### Prior shipped baseline (2026-03-27)

Shipped v0.1.0 to PyPI. MCP server working (6 tools: predict, verify, card, summary, list, trajectory). Used during real vigil engineering work (5 predictions, 4/5 correct). Added Trust Card badge generator. REVIEW.md grade A-. 96 tests. CI green. Commitment scheme has 9 tests including tamper detection.

### #1 Priority: Get one external user

REVIEW.md identified: no external users. caliber has only been used by Satish's own agent. Stranger validation needed to prove the tool is useful beyond its creator. Post in Claude Code community or AI agent forums.

### What NOT to do

- Don't add difficulty metrics yet — Phase 2 problem, needs more usage data first
- Don't rewrite storage — file-based JSON is fine for current scale
- Don't build verification for Trust Cards yet — needs the commitment scheme tested more first

---

## Work

### External adoption

_No strangers have used caliber. Need validation outside Satish's workflow._

- [ ] Write a "getting started" tutorial or blog post
- [ ] Post in Claude Code community / AI agent forums
- [ ] Collect feedback from first external user
- [ ] Adjust based on feedback

### Integration hardening

_MCP server works but integration points need polish._

- [ ] MCP config auto-apply — currently needs manual addition to ~/.mcp.json
- [x] Test multi-agent workflows (two agents with different Trust Cards) — 2026-05-11 · CLI regression covers shared-store separation and collision-prone agent names
- [x] Add `caliber trajectory` CLI command — verified 2026-05-10 · `tests/test_cli.py`
- [ ] Clean up extract_calibrate_md.py (standalone script → use `caliber import` command)

### Phase 2: Trust Card integrity (future)

_Deferred until more usage data exists._

- [ ] Difficulty metrics — detect trivial prediction farming
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

</details>

---

## Decision Log

| ID | Date | Decision | Why |
|----|------|----------|-----|
| D-001 | 2026-03-26 | Published as caliber-trust (not caliber) | Name taken by existing ML library. |
| D-002 | 2026-03-26 | SHA-256 commitment scheme for prediction anchoring | Cryptographic proof of timing without external services. Standard, simple. |

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

---

### Key reference files

| File | What it contains |
|------|-----------------|
| GAUGE.md | This file. |
| REVIEW.md | Structured assessment (grade A-). |
| CLAUDE.md | Detailed architecture + known issues + next steps. |
| INTEGRATIONS.md | How caliber connects to svx, engram, scroll, probe. |
