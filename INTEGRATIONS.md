# caliber — Integration Designs

> 2026-06-10: every integration that produces a prediction stream now gets
> gaming detection for free — `caliber_integrity` (MCP) / `caliber integrity`
> (CLI) runs deterministic farming/fabrication checks over any agent's store.
> Notes added per integration below.

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

**Integrity note:** automated svx→caliber feeds are exactly the workload
the integrity module was tuned for. Simulations of similar commands produce
templated claims (`template_claim_ratio` will be high — that is fine, it is
a metric, not a flag) and near-instant verification (simulate → execute →
verify within seconds). Before shipping this bridge, the INSTANT_VERIFICATION
flag needs an exemption path for event-driven feeds — e.g. svx-bridge
predictions carry a `notes` marker, or the bridge uses a dedicated agent
name whose report is read with that context. Known design constraint,
discovered by running integrity against live field data (the `default`
store's real predict→verify latency already trips it).

## engram Integration

engram stores cross-session knowledge. caliber generates Trust Cards.
If engram stored Trust Card snapshots, an agent could query its own
calibration history: "How was my security accuracy 10 sessions ago?"

**Implementation:** After generating a Trust Card, caliber stores a
snapshot in engram as a `calibration` entry type.

**Integrity note:** snapshots should be generated with
`caliber card --with-integrity` so the stored history carries its own
gaming analysis — a future session reading an old snapshot can see whether
the record behind it was witnessed or imported (UNWITNESSED_HISTORY).

## scroll Integration

scroll extracts knowledge from git history. If caliber's predictions
are committed to git (which they are in CALIBRATE.md format), scroll
could extract calibration trends from the git history.

**Implementation:** scroll reads CALIBRATE.md format from git diffs
and generates calibration trajectory data.

**Integrity note:** anything scroll backfills arrives without witnessed
timing and will (correctly) carry UNWITNESSED_HISTORY in integrity reports.
That is honest labeling, not a defect: backfilled history is context, only
live signed predictions are proof. Git commit timestamps could partially
witness CALIBRATE.md entries — a commit predates its diff content — which
would upgrade backfills from "unwitnessed" to "git-witnessed". Future idea.

## probe Integration

probe scans MCP server security. caliber IS an MCP server. probe
should be able to scan caliber's MCP configuration for security issues.

**Implementation:** Already possible — probe scans .mcp.json which
now includes caliber.
