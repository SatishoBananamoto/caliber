# caliber — CLAUDE.md

## What This Is

Trust protocol for AI agents. Tracks predictions with confidence levels,
generates Trust Cards showing calibration by confidence bucket and domain.

**Current reality check (2026-06-10):** v0.1.0 is published on PyPI as
`caliber-trust`. Core library, CLI, MCP server, importer, commitment scheme,
badge generation, trajectory support, and gaming-signature detection
(`caliber integrity`) are implemented. Fresh local check: 131 tests passing
with `python3 -B -m pytest -q -p no:cacheprovider`.

The original status snapshot below is retained as history, not current state.

**Status:** v0.1.0. Core library + CLI working. 46 tests passing. First
Trust Card generated from 51 real predictions.

## Quick Reference

```bash
# Run tests
cd ~/caliber && python3 -m pytest tests/ -v

# Import MY UNIVERSE data through the maintained CLI path
python3 -m caliber.cli -a claude-opus-my-universe import ~/MY\ UNIVERSE/CALIBRATE.md

# Compatibility wrapper for regenerating the sample Trust Card JSON
python3 extract_calibrate_md.py

# CLI usage
python3 -m caliber.cli -a agent-name predict "claim" -c 80 -d domain
python3 -m caliber.cli -a agent-name verify <id> --correct
python3 -m caliber.cli -a agent-name card [--json]
python3 -m caliber.cli mcp-config --install --path ~/.mcp.json --cwd ~/caliber
```

## Architecture

```
caliber/
├── tracker.py      # TrustTracker + Prediction (core)
├── card.py         # TrustCard (buckets, significance, danger/strength zones)
├── storage.py      # FileStorage (JSON) + MemoryStorage (tests)
├── cli.py          # Click CLI (predict, verify, card, summary, list, import, trajectory, integrity)
├── mcp_server.py   # FastMCP server (7 tools)
├── trajectory.py   # Trajectory analysis (snapshots, trends)
├── integrity.py    # Gaming-signature detection (Murphy decomposition + behavioral flags)
├── commitment.py   # SHA-256 prediction anchoring
├── importer.py     # Import from CALIBRATE.md and CSV
└── __init__.py     # Public API
```

## Known Issues / Remaining Work

1. ~~**MCP config not auto-applied.**~~ `caliber mcp-config --install`
   now merges the MCP server entry into a chosen JSON config and keeps a
   timestamped backup when updating an existing file.

2. ~~**extract_calibrate_md.py is still standalone.**~~ The script now uses
   the shared importer and remains only as a backwards-compatible Trust Card
   JSON wrapper.

3. ~~**Difficulty metrics not implemented.**~~ `caliber/integrity.py`
   (2026-06-10) detects trivial-prediction farming via Murphy decomposition
   of the Brier score plus behavioral signals (concentration, duplicates,
   verify latency, import share). Deliberately behavioral statistics, not
   claim-text NLP — claim scoring is itself gameable (GAUGE D-003).
   Cross-agent difficulty comparison remains future work.

4. **Verification subjectivity unaddressed.** Who decides "correct"?
   For filesystem checks: objective. For code review: subjective.
   Phase 2 problem.

5. **No PyPI package.** Local install only. Need to publish.
   - 2026-05-11 update: superseded. The package is published as
     `caliber-trust`; remaining adoption work is external-user validation.

## Next Steps

The original list below is retained as a historical snapshot. Current priority
is external-user validation plus Phase 2 Trust Card verification after more
usage data. Multi-agent CLI workflows now have regression coverage for
separate Trust Cards in a shared store.

1. **PyPI publishing** — `pip install caliber`
2. **Difficulty metrics** — detect trivial prediction farming
3. **Trust Card verification** — chi-square on distributions, consistency checks
4. **A2A Agent Card extension** — add calibration data to Agent Cards

## Origin

Extracted from MY UNIVERSE (~/MY UNIVERSE/) — Claude's cognitive workspace.
The calibration practice revealed patterns (danger zones, evidence quality)
that became caliber's core features. See PLAN-TRUST-LAYER.md in MY UNIVERSE.

<!-- scroll:start -->
## Project Knowledge (scroll)

*Extracted from `caliber` git history.*

### Decisions

- **DEC-001**: Changed PyPI distribution name from 'caliber' to 'caliber-trust' (high)
  - The original name 'caliber' was already taken by an existing ML library by gianlucadetommaso. The alternative 'agent-trust' was too similar to existing projects. 'caliber-trust' was available and clearly indicates the purpose.
- **DEC-002**: Implemented commitment scheme using SHA-256 for prediction anchoring (high)
  - Provides cryptographic proof of prediction timing without requiring external services or blockchain infrastructure. Uses standard SHA-256 with random salt for security. TrustTracker(signed=True) automatically creates commitments for seamless integration.

### Known Mistakes

- **MST-001**: Importer regex was too strict, causing data import failures (high)
  - Made the regex more flexible to handle entries with single newline after header, improving import success rate to 77/87 entries.

### Learnings

- **LRN-001**: SVX integration identified as highest value for automatic calibration data generation (high)
  - SVX integration provides the most value by automatically converting safety simulations into calibration data, enabling proof of safety layer effectiveness through accumulated evidence rather than assertions.

### Observations

- **OBS-001**: Enhanced summary feedback improves early user engagement before sufficient data accumulation (high)
  - Addresses the cold start problem in calibration tracking by providing immediate value and clear progress indicators, encouraging continued usage until meaningful statistical analysis becomes available.

### Goals

- **GOL-001**: Complete Phase 1 v0.1 design implementation (high)
  - All v0.1 design debts resolved with working implementations of core calibration tracking features.

<!-- scroll:end -->
