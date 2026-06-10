# Getting Started With caliber

This guide is for a first external user who wants to test whether calibration
tracking is useful in normal agent or coding work.

caliber works best when the prediction is made before checking the answer. The
point is not to look smart. The point is to leave evidence about when an agent
is reliable, overconfident, underconfident, or weak in a specific domain.

## 1. Install

```bash
pip install caliber-trust
```

If you are testing from a local checkout:

```bash
python3 -m pip install -e .
```

## 2. Pick An Agent Name

Use one stable name for the agent or workflow you want to measure:

```bash
export AGENT_NAME=my-code-agent
```

For multiple agents, use different names. caliber stores each agent separately
and generates a separate Trust Card for each one.

## 3. Make Three Predictions Before Checking

Choose quick predictions with objective outcomes. Good first domains are
`codebase`, `test`, `api`, `docs`, `security`, and `architecture`.

```bash
caliber -a "$AGENT_NAME" predict "the repository has a pytest config" -c 70 -d codebase
caliber -a "$AGENT_NAME" predict "the main package exposes a CLI entry point" -c 80 -d api
caliber -a "$AGENT_NAME" predict "the README documents installation" -c 90 -d docs
```

Each command prints a prediction ID. Keep those IDs for verification.

## 4. Check The Facts

Now inspect the repo, run the command, or open the file. Then verify each
prediction:

```bash
caliber -a "$AGENT_NAME" verify <prediction-id> --correct
caliber -a "$AGENT_NAME" verify <prediction-id> --incorrect --notes "README has usage but no install command"
```

Use `--incorrect` when the claim was materially wrong. Use `--notes` for the
lesson, not for self-justification.

## 5. Read The Early Summary

After a few predictions:

```bash
caliber -a "$AGENT_NAME" summary
```

Early data is directional only. It can still reveal useful patterns, such as an
agent being good at file-count predictions but weak at behavior predictions.

## 6. Generate A Trust Card

After enough verified predictions:

```bash
caliber -a "$AGENT_NAME" card
caliber -a "$AGENT_NAME" card --json
```

The Trust Card answers:

- how many predictions were verified
- overall accuracy
- mean confidence
- confidence-bucket calibration
- domain strengths and weaknesses
- danger zones where confidence is unreliable

Treat small buckets carefully. caliber flags insufficient data and statistical
significance so a few lucky or unlucky predictions do not become a fake pattern.

## 7. Check Your Record For Gaming Signatures

```bash
caliber -a "$AGENT_NAME" integrity
```

A Trust Card proves calibration, but calibration can be farmed with easy
predictions. The integrity report runs deterministic checks — outcome
variance, confidence concentration, duplicate claims, verification latency,
and a too-good-to-be-true test for fabricated outcomes — and reports
advisory flags with evidence.

With only a few predictions it will say there is insufficient data. That is
honest, not broken: the checks gate on minimum sample sizes. Run it again
after 20+ verified predictions, and attach it when sharing a card:

```bash
caliber -a "$AGENT_NAME" card --with-integrity
```

## 8. Import Existing Calibration Data

If you already have a MY UNIVERSE-style `CALIBRATE.md`:

```bash
caliber -a "$AGENT_NAME" import CALIBRATE.md
caliber -a "$AGENT_NAME" card
```

CSV imports are also supported with columns:

```text
claim,confidence,domain,correct,notes
```

Imported history will carry an UNWITNESSED_HISTORY note in integrity
reports — the predictions arrived with their outcomes, so timing cannot be
independently verified. Live predictions you make going forward do not have
this caveat.

## 9. Use MCP From An Agent

Print the MCP config snippet:

```bash
caliber mcp-config --cwd /path/to/caliber
```

Install it into a chosen MCP JSON file:

```bash
caliber mcp-config --install --path ~/.mcp.json --cwd /path/to/caliber
```

When updating an existing config, caliber writes a timestamped backup first.

## First Feedback To Send Back

If you try caliber, the most useful feedback is concrete:

- Was it clear when to make a prediction?
- Did recording predictions change what the agent checked?
- Did any confidence number feel forced or fake?
- Which command or output was confusing?
- After 10 to 20 predictions, did the summary reveal a real pattern?

That feedback matters more than a broad opinion like "useful" or "not useful."
