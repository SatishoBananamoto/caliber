# caliber — Integration Designs

## svx Integration

svx simulates command outcomes before execution. Each simulation IS a
prediction. If caliber tracked svx's predictions against actual outcomes,
you'd get automatic calibration of the safety layer.

```
Agent proposes: rm -rf ./build
→ svx simulates: "directory will be deleted, 47 files affected"
→ caliber records: predict("build dir deletion removes 47 files", 0.90, "safety")
→ Agent executes
→ Outcome observed: 47 files deleted
→ caliber records: verify(correct=True)
```

**What this enables:** The Trust Card shows "svx simulation accuracy: 92%
(85 predictions). Danger zone: none." This PROVES the safety layer works —
not by assertion, but by accumulated evidence.

**Implementation:** svx MCP server emits a `simulation_complete` event.
caliber MCP server listens and creates a prediction from the simulation.
After execution, svx emits `execution_complete` and caliber verifies.

**Status:** Design only. Requires both MCP servers running and an event
bridge between them.

## engram Integration

engram stores cross-session knowledge. caliber generates Trust Cards.
If engram stored Trust Card snapshots, an agent could query its own
calibration history: "How was my security accuracy 10 sessions ago?"

**Implementation:** After generating a Trust Card, caliber stores a
snapshot in engram as a `calibration` entry type.

## scroll Integration

scroll extracts knowledge from git history. If caliber's predictions
are committed to git (which they are in CALIBRATE.md format), scroll
could extract calibration trends from the git history.

**Implementation:** scroll reads CALIBRATE.md format from git diffs
and generates calibration trajectory data.

## probe Integration

probe scans MCP server security. caliber IS an MCP server. probe
should be able to scan caliber's MCP configuration for security issues.

**Implementation:** Already possible — probe scans .mcp.json which
now includes caliber.
