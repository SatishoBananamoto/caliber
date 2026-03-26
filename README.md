# caliber

Trust protocol for AI agents. Prove capability through calibration, not claims.

## The Problem

Every agent registry — Google's A2A, Microsoft's Entra, Salesforce's MuleSoft — faces the same problem: agents describe what they *can* do, not how *well* they do it. Agent Cards are LinkedIn profiles with no work history.

When Agent A asks Agent B for help, there's no way to know if B is actually good at the task. B says it can review code. Can it? With what accuracy? Is it overconfident? Does it know its own blind spots?

## The Solution

caliber tracks predictions with confidence levels and generates **Trust Cards** — machine-readable credentials that prove an agent's calibration through accumulated evidence.

A Trust Card answers:
- **Overall:** How accurate is this agent?
- **By confidence:** When it says "80% sure," is it right 80% of the time?
- **By domain:** Where is it strong? Where is it weak?
- **Danger zones:** Confidence ranges where the agent is systematically overconfident.

## Quick Start

```bash
pip install git+https://github.com/SatishoBananamoto/caliber.git
```

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

```json
{
  "trust_version": "0.1",
  "agent_name": "my-code-reviewer",
  "generated": "2026-03-26T00:00:00Z",
  "calibration": {
    "total_predictions": 77,
    "total_verified": 77,
    "overall_accuracy": 0.766,
    "mean_confidence": 0.708,
    "mean_calibration_gap": -0.058,
    "confidence_buckets": {
      "50-59": {"predictions": 4, "correct": 2, "accuracy": 0.5, "calibration_gap": 0.045, "insufficient_data": true},
      "60-69": {"predictions": 25, "correct": 16, "accuracy": 0.64, "calibration_gap": 0.005, "significant": false},
      "70-79": {"predictions": 29, "correct": 24, "accuracy": 0.828, "calibration_gap": -0.083, "significant": false},
      "80-89": {"predictions": 18, "correct": 16, "accuracy": 0.889, "calibration_gap": -0.044, "significant": false},
      "90-99": {"predictions": 1, "correct": 1, "accuracy": 1.0, "calibration_gap": -0.055, "insufficient_data": true}
    },
    "domains": {
      "architecture": {"predictions": 21, "accuracy": 0.81},
      "behavior": {"predictions": 25, "accuracy": 0.64},
      "codebase": {"predictions": 20, "accuracy": 0.75}
    },
    "strength_zones": ["50-59"]
  }
}
```

The Trust Card above is real — generated from 77 calibration predictions made by Claude Opus during the [MY UNIVERSE](https://github.com/SatishoBananamoto/my-universe) project.

**What the numbers reveal:** This agent is well-calibrated overall. Each bucket includes a `significant` field (binomial test, p<0.05) and flags `insufficient_data` for small samples. No bucket shows statistically significant miscalibration — the agent's confidence matches its accuracy. Behavior predictions (64%) are its weakest domain.

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

Confidence ranges where the calibration gap exceeds 10 percentage points with at least 3 data points. These are the ranges where the agent's self-assessment is unreliable.

## Origin

caliber emerged from [MY UNIVERSE](https://github.com/SatishoBananamoto/my-universe), a cognitive workspace where Claude Opus tracks its own predictions and calibration. 87 predictions across 3 sessions validated the approach — and revealed that early "danger zone" findings were small-sample artifacts, corrected by caliber's own statistical significance tests.

The thesis: if calibration tracking works for self-improvement, it works for trust between agents. caliber includes the statistical honesty features because we learned the hard way that small samples lie.

## Roadmap

- **v0.1** (current): Core tracker, CLI, MCP server, Trust Card generation with statistical significance tests
- **v0.2**: Trust Card verification (detect fabricated/gamed cards), trajectory support
- **v0.3**: A2A Agent Card extension, commitment scheme (prediction anchoring)
- **v1.0**: Signed cards, trust registry, cross-agent trust queries

## MCP Server

For AI agents that want to track calibration natively:

```bash
python -m caliber.mcp_server
```

Or add to `.mcp.json`:

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

Tools: `caliber_predict`, `caliber_verify`, `caliber_card`, `caliber_summary`, `caliber_list`.

The prediction log doubles as a decision audit trail — observability as a side effect of calibration.

## Statistical Honesty

Trust Cards include per-bucket significance tests (binomial, p<0.05) and flag insufficient data (<5 predictions per bucket). This prevents treating small-sample noise as calibration patterns — a real problem we discovered building this.

## License

MIT
