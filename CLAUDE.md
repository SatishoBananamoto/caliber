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
├── tracker.py    # TrustTracker + Prediction dataclass (core)
├── card.py       # TrustCard generation (confidence buckets, danger zones)
├── storage.py    # FileStorage (JSON) + MemoryStorage (tests)
├── cli.py        # Click-based CLI
└── __init__.py   # Public API: TrustTracker, Prediction, TrustCard
```

## Known Issues / Design Debts

1. **danger_zones only flags overconfident buckets.** Doesn't show
   "strength zones" where agent is underconfident (accuracy > confidence).
   Should flag both directions. (P-057 discovery)

2. **0.10 threshold for danger zone is feeling-based AND underpowered.**
   Binomial tests show NO bucket-level findings are significant at p<0.10
   with current sample sizes (3-22 per bucket). The Trust Card should
   include significance tests (binomial p-values per bucket) and flag
   underpowered results. Critical: without this, users will treat noise
   as patterns, exactly as MY UNIVERSE did for 3 sessions.

3. **No import CLI command.** extract_calibrate_md.py is standalone.
   Should be integrated as `caliber import`.

4. **No trajectory support.** Trust Card is a snapshot. Should show
   how calibration changes over time (trajectory insight from session 3).

5. **No prediction anchoring.** Trust Cards can be fabricated. Need
   commitment scheme (hash-based, Pre-Mortem from session 3).

## Next Steps (Priority Order)

1. **MCP server** (Phase 1.5) — enables agent-native calibration tracking.
   Design sketch in ~/MY UNIVERSE/ANALYSES.md. ~150 lines.
2. **GitHub repo + PyPI** — shipping.
3. **Strength zones** — flag underconfident buckets (negative cal gap).
4. **Trajectory** — snapshot series in Trust Card format.
5. **Commitment scheme** — SHA-256 prediction anchoring.

## Origin

Extracted from MY UNIVERSE (~/MY UNIVERSE/) — Claude's cognitive workspace.
The calibration practice revealed patterns (danger zones, evidence quality)
that became caliber's core features. See PLAN-TRUST-LAYER.md in MY UNIVERSE.
