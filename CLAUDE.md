# caliber — CLAUDE.md

## What This Is

Trust protocol for AI agents. Tracks predictions with confidence levels,
generates Trust Cards showing calibration by confidence bucket and domain.

**Status:** v0.1.0. Core library + CLI working. 46 tests passing. First
Trust Card generated from 51 real predictions.

## Quick Reference

```bash
# Run tests
cd ~/caliber && python3 -m pytest tests/ -v

# Generate Trust Card from MY UNIVERSE data
python3 extract_calibrate_md.py

# CLI usage
python3 -m caliber.cli -a agent-name predict "claim" -c 80 -d domain
python3 -m caliber.cli -a agent-name verify <id> --correct
python3 -m caliber.cli -a agent-name card [--json]
```

## Architecture

```
caliber/
├── tracker.py      # TrustTracker + Prediction (core)
├── card.py         # TrustCard (buckets, significance, danger/strength zones)
├── storage.py      # FileStorage (JSON) + MemoryStorage (tests)
├── cli.py          # Click CLI (predict, verify, card, summary, list, import, trajectory)
├── mcp_server.py   # FastMCP server (6 tools)
├── trajectory.py   # Trajectory analysis (snapshots, trends)
├── commitment.py   # SHA-256 prediction anchoring
├── importer.py     # Import from CALIBRATE.md and CSV
└── __init__.py     # Public API
```

## Known Issues / Remaining Work

1. **MCP config not auto-applied.** Needs manual addition to ~/.mcp.json.
   Config is already added for this machine.

2. **extract_calibrate_md.py is still standalone.** The `caliber import`
   CLI command exists, but the standalone script remains for backwards compat.

3. **Difficulty metrics not implemented.** Trust Cards can be gamed by
   making only easy predictions. Need claim specificity scoring or
   cross-agent comparison. Phase 2 problem.

4. **Verification subjectivity unaddressed.** Who decides "correct"?
   For filesystem checks: objective. For code review: subjective.
   Phase 2 problem.

5. **No PyPI package.** Local install only. Need to publish.

## Next Steps

1. **PyPI publishing** — `pip install caliber`
2. **Difficulty metrics** — detect trivial prediction farming
3. **Trust Card verification** — chi-square on distributions, consistency checks
4. **A2A Agent Card extension** — add calibration data to Agent Cards

## Origin

Extracted from MY UNIVERSE (~/MY UNIVERSE/) — Claude's cognitive workspace.
The calibration practice revealed patterns (danger zones, evidence quality)
that became caliber's core features. See PLAN-TRUST-LAYER.md in MY UNIVERSE.
