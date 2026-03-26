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
pip install caliber
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
```

## Trust Card Format

```json
{
  "trust_version": "0.1",
  "agent_name": "my-code-reviewer",
  "generated": "2026-03-26T00:00:00Z",
  "calibration": {
    "total_predictions": 36,
    "total_verified": 36,
    "overall_accuracy": 0.75,
    "mean_confidence": 0.729,
    "mean_calibration_gap": 0.001,
    "confidence_buckets": {
      "50-59": {"predictions": 2, "correct": 2, "accuracy": 1.0, "calibration_gap": -0.455},
      "60-69": {"predictions": 8, "correct": 4, "accuracy": 0.5, "calibration_gap": 0.145},
      "70-79": {"predictions": 13, "correct": 9, "accuracy": 0.692, "calibration_gap": 0.053},
      "80-89": {"predictions": 12, "correct": 11, "accuracy": 0.917, "calibration_gap": -0.072},
      "90-99": {"predictions": 1, "correct": 1, "accuracy": 1.0, "calibration_gap": -0.055}
    },
    "domains": {
      "architecture": {"predictions": 9, "accuracy": 0.778},
      "behavior": {"predictions": 15, "accuracy": 0.6},
      "codebase": {"predictions": 6, "accuracy": 0.833}
    },
    "danger_zones": ["60-69"]
  }
}
```

The Trust Card above is real — generated from 36 calibration predictions made by Claude Opus during the [MY UNIVERSE](https://github.com/SatishoBananamoto/my-universe) project.

**What the numbers reveal:** This agent is well-calibrated overall (0.1% gap), but has a **danger zone at 60-69% confidence** where it's only 50% accurate despite claiming ~65%. It's actually *underconfident* at 80-89% (91.7% accurate). Behavior predictions are its weakest domain (60%).

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

caliber emerged from [MY UNIVERSE](https://github.com/SatishoBananamoto/my-universe), a cognitive workspace where Claude Opus tracks its own predictions and calibration. The 36-prediction dataset that generated the first Trust Card revealed patterns — like the 60-69% danger zone — that wouldn't be visible from overall accuracy alone.

The thesis: if calibration tracking works for self-improvement, it works for trust between agents.

## Roadmap

- **v0.1** (current): Core tracker, Trust Card generation, CLI, flat-file storage
- **v0.2**: Trust Card verification (detect fabricated/gamed cards)
- **v0.3**: A2A Agent Card extension, MCP server mode
- **v1.0**: Signed cards, trust registry, cross-agent trust queries

## License

MIT
