# caliber

Calibration instrument for AI agents — measure it, stress-test it, prove it.

## The Problem

Agent registries, model cards, and tool manifests describe what an agent *can*
do, not how well it does the work over time. Capability claims need measured
history.

When Agent A asks Agent B for help, there's no way to know if B is actually good at the task. B says it can review code. Can it? With what accuracy? Is it overconfident? Does it know its own blind spots?

## The Solution

caliber tracks predictions with confidence levels and generates **Trust Cards**
— machine-readable calibration records backed by accumulated outcomes,
uncertainty estimates, adversarial stress tests, and tamper-evident logs.

A Trust Card answers:
- **Overall:** How accurate is this agent?
- **By confidence:** When it says "80% sure," is it right 80% of the time?
- **By domain:** Where is it strong? Where is it weak?
- **Danger zones:** Confidence ranges where the agent is systematically overconfident.

A Trust Card is not a universal proof of competence. It is evidence about the
record it was generated from, with explicit limits documented below.

## Quick Start

```bash
pip install caliber-trust
```

For a first external-user walkthrough, see [GETTING_STARTED.md](GETTING_STARTED.md).

### Python API

```python
from caliber import TrustTracker

tracker = TrustTracker("my-code-reviewer", store_path="./trust-data")

# Record a prediction before checking
pid = tracker.predict(
    claim="this function has a SQL injection vulnerability",
    confidence=0.85,
    domain="security"
)

# After verifying
tracker.verify(pid, correct=True, notes="Found in line 42")

# Generate a Trust Card
card = tracker.generate_card()
print(card.summary())
print(card.to_json())  # Machine-readable
```

### CLI

```bash
# Make a prediction
caliber -a my-agent predict "this endpoint returns JSON" -c 90 -d api

# Verify it
caliber -a my-agent verify <prediction-id> --correct

# Generate Trust Card
caliber -a my-agent card
caliber -a my-agent card --json

# Quick progress check
caliber -a my-agent summary

# Show calibration trajectory over time
caliber -a my-agent trajectory --interval 10

# Check the record for gaming signatures
caliber -a my-agent integrity

# Verify event logs and saved cards
caliber -a my-agent verify-log
caliber -a my-agent anchor
caliber -a my-agent verify-card card.json

# Import existing calibration data
caliber -a my-agent import CALIBRATE.md

# Convert a legacy JSON snapshot into an event log
caliber -a my-agent migrate
```

### Try It Now

Make 3 predictions about your codebase before checking:

```bash
caliber predict "src/ has more than 10 Python files" -c 70 -d codebase
caliber predict "package.json has a test script" -c 85 -d codebase
caliber predict "the main module uses asyncio" -c 60 -d architecture
```

Then verify each one:

```bash
caliber verify <id1> --correct   # or --incorrect
caliber verify <id2> --correct
caliber verify <id3> --incorrect
```

After 3 predictions: `caliber summary`. After 20: `caliber card`.

## Trust Card Format

Excerpt from the regenerated `trust-card-claude-opus.json` artifact:

```json
{
  "trust_version": "0.1",
  "agent_name": "claude-opus-my-universe",
  "generated": "2026-07-04T08:34:03.135853+00:00",
  "calibration": {
    "total_predictions": 94,
    "total_verified": 94,
    "overall_accuracy": 0.755,
    "mean_confidence": 0.707,
    "mean_calibration_gap": -0.048,
    "brier_score": 0.1798,
    "reliability": 0.0205,
    "resolution": 0.0255,
    "uncertainty": 0.1848,
    "calibration_z": 1.0537,
    "calibration_p": 0.292,
    "confidence_buckets": {
      "50-59": {"predictions": 6, "correct": 4, "mean_confidence": 0.542, "accuracy": 0.667, "ci95": [0.3, 0.903], "calibration_gap": -0.125, "significant": false},
      "60-69": {"predictions": 30, "correct": 19, "mean_confidence": 0.625, "accuracy": 0.633, "ci95": [0.455, 0.781], "calibration_gap": -0.008, "significant": false},
      "70-79": {"predictions": 34, "correct": 28, "mean_confidence": 0.719, "accuracy": 0.824, "ci95": [0.665, 0.917], "calibration_gap": -0.104, "significant": false},
      "80-89": {"predictions": 22, "correct": 19, "mean_confidence": 0.825, "accuracy": 0.864, "ci95": [0.667, 0.953], "calibration_gap": -0.039, "significant": false},
      "90-99": {"predictions": 2, "correct": 1, "mean_confidence": 0.925, "accuracy": 0.5, "ci95": [0.095, 0.905], "calibration_gap": 0.425, "insufficient_data": true}
    },
    "adaptive_buckets": [
      {"index": 1, "predictions": 23, "accuracy": 0.565, "mean_confidence": 0.589, "ci95": [0.368, 0.744]},
      {"index": 2, "predictions": 24, "accuracy": 0.75, "mean_confidence": 0.673, "ci95": [0.551, 0.88]},
      {"index": 3, "predictions": 23, "accuracy": 0.87, "mean_confidence": 0.728, "ci95": [0.679, 0.955]},
      {"index": 4, "predictions": 24, "accuracy": 0.833, "mean_confidence": 0.833, "ci95": [0.641, 0.933]}
    ],
    "domains": {
      "architecture": {"predictions": 21, "accuracy": 0.81},
      "behavior": {"predictions": 31, "accuracy": 0.645},
      "codebase": {"predictions": 25, "accuracy": 0.76},
      "self": {"predictions": 9, "accuracy": 0.778}
    }
  }
}
```

The full artifact is generated from 94 verified predictions in the local MY UNIVERSE calibration corpus.

**What the numbers reveal:** This agent is slightly underconfident overall: 75.5% accuracy against 70.7% mean confidence. No fixed confidence bucket is a danger or strength zone because none has statistically significant miscalibration. The 90-99% bucket has a large apparent gap, but only 2 predictions, so it is marked `insufficient_data` rather than promoted into a zone. Behavior predictions are still the weakest domain at 64.5% accuracy.

## Key Concepts

### Confidence Buckets

The core insight: overall accuracy is meaningless without calibration. An agent that's "75% accurate" could be perfectly calibrated (right 75% of the time at 75% confidence) or dangerously miscalibrated (right 50% of the time while claiming 90% confidence).

Confidence buckets break accuracy down by confidence level, revealing where the agent knows its limits and where it doesn't.

### Calibration Gap

The difference between expected and actual accuracy for each confidence bucket:
- **Positive gap** = overconfident (accuracy < confidence)
- **Negative gap** = underconfident (accuracy > confidence)
- **Near zero** = well-calibrated

### Danger Zones

Confidence ranges where the calibration gap exceeds 10 percentage points and the exact binomial significance test passes. Buckets with fewer than 5 predictions are marked `insufficient_data` and cannot become danger or strength zones by themselves.

## Gaming Detection

Calibration alone can be farmed: predict "this file exists" at 99% a hundred times and the Trust Card looks flawless. `caliber integrity` detects that signature with deterministic statistics — no claim judging, no LLM:

```bash
caliber integrity            # human-readable report
caliber integrity --json     # machine-readable
caliber card --with-integrity  # attach it to the Trust Card
```

The core is the Murphy decomposition of the Brier score (`reliability - resolution + uncertainty`). A farmer can fake reliability (calibration), but not **resolution** — discriminating outcomes requires taking real predictive risk — and not **uncertainty**: if nearly every prediction came true, the outcome set was a foregone conclusion and the card proves little.

Supporting signals: confidence concentration in the top bucket, domain concentration (Herfindahl index), duplicate claims, predict→verify latency (instant verification suggests the answer was already known), and batch-import share (history without witnessed timing).

There is also a too-good-to-be-true check: a forger who *fabricates* outcomes to match stated confidence evades every behavioral signal, but real binomial outcomes scatter — observed accuracy that tracks confidence more tightly than chance permits raises `SUSPICIOUSLY_PERFECT` (the same lower-tail test that exposed Mendel's pea data). The adversarial strategies and their countermeasures are encoded in `tests/test_integrity_adversarial.py`.

Findings are advisory flags with evidence, gated on minimum sample sizes. There is deliberately no aggregate integrity score — a single number would itself become the gaming target. Signals that cannot distinguish gaming from honest bulk use (e.g. templated claims) are reported as metrics, never flags.

## Threat Model And Verification

Caliber proves different things at different evidence levels:

- **Record only:** calibration, confidence-bucket behavior, domain breakdowns,
  and advisory gaming signatures over the stored predictions.
- **Event log:** edited, deleted, or reordered history breaks the hash chain.
- **Anchored head:** anyone with the saved head can detect later rewrites from
  that anchor forward.
- **External adjudication:** semantic task difficulty and outcome judgment
  still need domain review outside Caliber.

New stores write an append-only JSONL event log beside the JSON snapshot. The
event log is the source of truth; the JSON file remains a derived cache for
backward-compatible readers. Each event carries `prev_hash`, the SHA-256 hash
of the previous raw event line.

```bash
caliber -a my-agent verify-log              # verify the hash chain
caliber -a my-agent anchor                  # append/print an anchor event
caliber -a my-agent verify-log --head <h>   # compare with a saved head
caliber -a my-agent verify-card card.json   # recompute card stats from the log
```

`caliber migrate` converts an older JSON-only store into an event log by
marking existing records as imported/migrated history. That is intentionally
honest: the new chain proves future ordering, not that old predictions were
witnessed when originally made.

Commitment hashes bind prediction fields to a salted hash, but unanchored
commitments stored with the same mutable local data are self-attestation. Third
parties get tamper evidence only after they have an externally saved chain
head, for example the `New head` printed by `caliber anchor`.

## Origin

caliber emerged from a local MY UNIVERSE calibration practice where Claude Opus tracked its own predictions and calibration. The current source corpus parses to 94 verified predictions — and revealed that early "danger zone" findings were small-sample artifacts, corrected by caliber's own statistical significance tests.

The thesis: if calibration tracking improves one agent's self-assessment, the
same evidence can help humans and agent systems decide when to rely on that
agent. caliber includes the statistical honesty features because we learned the
hard way that small samples lie.

## Roadmap

- **v0.1**: Core tracker, CLI, MCP server, Trust Card generation, import, trajectory support
- **v0.2** (current): Statistical Trust Cards plus gaming-signature detection (`caliber integrity`)
- **v0.3** (northstar branch, not yet published): Hash-chained event logs, `verify-log`, `anchor`, `migrate`, and `verify-card`
- **v0.4**: A2A Agent Card extension
- **v1.0**: Signed cards, trust registry, cross-agent trust queries

## MCP Server

For AI agents that want to track calibration natively:

```bash
python -m caliber.mcp_server
```

Print the MCP config snippet:

```bash
caliber mcp-config --cwd /path/to/caliber
```

Or install it into `.mcp.json` with a timestamped backup if the file already
exists:

```bash
caliber mcp-config --install --path ~/.mcp.json --cwd /path/to/caliber
```

The installed entry has this shape:

```json
{
  "mcpServers": {
    "caliber": {
      "command": "python3",
      "args": ["-m", "caliber.mcp_server"],
      "cwd": "/path/to/caliber"
    }
  }
}
```

Tools: `caliber_predict`, `caliber_verify`, `caliber_card`, `caliber_summary`, `caliber_list`, `caliber_trajectory`, `caliber_integrity`.

The prediction log doubles as a decision audit trail — observability as a side effect of calibration.

## Statistical Honesty

Trust Cards include per-bucket significance tests (binomial, p<0.05) and flag insufficient data (<5 predictions per bucket). This prevents treating small-sample noise as calibration patterns — a real problem we discovered building this.

## License

MIT
