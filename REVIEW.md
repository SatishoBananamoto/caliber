# caliber — Review

## v1 — 2026-03-27

**Reviewer**: Claude (Opus 4.6, partner session)
**Version Reviewed**: v0.1.0, 12 source modules, 94 tests, on PyPI as caliber-trust
**Grade: A-** — Shipped to PyPI, used in real engineering work, genuine value demonstrated. Needs more external validation and the commitment scheme needs testing.

### Summary

caliber emerged from MY UNIVERSE's calibration practice — 100 predictions made and tracked across 3 sessions. The core insight (overall accuracy is meaningless without per-bucket calibration) was validated empirically, including the discovery that early "danger zone" findings were small-sample artifacts corrected by caliber's own statistical significance tests.

The tool was used during real vigil engineering work (5 predictions, 4/5 correct). The MCP server integrated with Claude Code. The CLI works. The importer handles MY UNIVERSE's format. The Trust Card format includes significance testing. The trajectory feature shows calibration over time.

### Strengths

1. **Born from real use.** Not designed from spec — extracted from working practice. The API reflects actual prediction-verify workflow.
2. **Statistical honesty.** Binomial significance tests on every bucket. Flags insufficient data. This prevented building on noise.
3. **MCP server.** caliber_predict/verify/card/summary tools available to agents natively. First real usage during vigil work.
4. **Importer.** Handles the CALIBRATE.md format from MY UNIVERSE. Bridge between practice and tooling.
5. **On PyPI.** `pip install caliber-trust` works. README is comprehensive.

### Weaknesses

1. **No external users.** Only used by the author's agent. Needs stranger validation.
2. **Commitment scheme untested.** SHA-256 anchoring exists but no tests verify it prevents tampering.
3. **No Trust Card verification.** Can't detect fabricated cards. Roadmap item.
4. **Storage is file-based JSON.** Won't scale for high-volume agents. Fine for now.
5. **CLI assumes single agent.** `-a` flag exists but multi-agent workflows haven't been tested.

### Recommendations

1. **Write commitment scheme tests.** Verify tampering detection works.
2. **Test multi-agent workflows.** Two agents with different Trust Cards.
3. **Add trajectory to CLI.** `caliber trajectory` command.
4. **Get one external user.** Post in Claude Code community or AI agent forums.

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| No users find it | High | Medium | Marketing, community posts |
| Commitment scheme has holes | Medium | High | Test coverage |
| A2A Agent Card format changes | Low | Medium | Modular extension design |
| PyPI name collision confusion | Low | Low | Clear README distinguishing from ML caliber |
