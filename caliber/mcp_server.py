"""MCP server for caliber — enables agent-native calibration tracking.

Agents can track predictions, verify outcomes, and generate Trust Cards
through MCP tool calls. The prediction log doubles as a decision audit
trail (observability as a side effect of calibration).

Usage:
    python -m caliber.mcp_server

Or add to Claude Code MCP config:
    {
        "mcpServers": {
            "caliber": {
                "command": "python3",
                "args": ["-m", "caliber.mcp_server"]
            }
        }
    }
"""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from caliber.tracker import TrustTracker
from caliber.storage import FileStorage

DEFAULT_STORE = Path.home() / ".caliber"
DEFAULT_AGENT = "default"

server = FastMCP("caliber", instructions=(
    "caliber tracks predictions with confidence levels and generates "
    "Trust Cards showing calibration by confidence bucket and domain. "
    "Use caliber_predict before checking something, caliber_verify after."
))

# Global tracker registry — one per agent name
_trackers: dict[str, TrustTracker] = {}
_storage = FileStorage(DEFAULT_STORE)


def _get_tracker(agent: str = DEFAULT_AGENT) -> TrustTracker:
    if agent not in _trackers:
        _trackers[agent] = TrustTracker(agent, storage=_storage)
    return _trackers[agent]


@server.tool()
def caliber_predict(
    claim: str,
    confidence: float,
    domain: str,
    agent: str = DEFAULT_AGENT,
    prediction_id: str = "",
) -> str:
    """Record a prediction before verifying it.

    Args:
        claim: What you expect to find (e.g. "this file has >200 lines").
        confidence: How confident, 50-99 or 0.50-0.99.
        domain: Category (codebase, behavior, architecture, facts, etc.)
        agent: Agent name. Defaults to "default".
        prediction_id: Optional explicit ID.

    Returns:
        The prediction ID for later verification.
    """
    if confidence >= 1.0:
        confidence = confidence / 100

    tracker = _get_tracker(agent)
    pid = tracker.predict(
        claim,
        confidence=confidence,
        domain=domain,
        prediction_id=prediction_id or None,
    )
    return f"Prediction recorded: {pid} ({confidence:.0%} confidence, {domain})"


@server.tool()
def caliber_verify(
    prediction_id: str,
    correct: bool,
    notes: str = "",
    agent: str = DEFAULT_AGENT,
) -> str:
    """Record the outcome of a prediction.

    Args:
        prediction_id: The ID from caliber_predict.
        correct: Was the prediction correct?
        notes: What this reveals about calibration.
        agent: Agent name.
    """
    tracker = _get_tracker(agent)
    pred = tracker.verify(prediction_id, correct=correct, notes=notes or None)
    result = "correct" if correct else "incorrect"
    return f"Verified {prediction_id}: {result}"


@server.tool()
def caliber_card(
    agent: str = DEFAULT_AGENT,
) -> dict:
    """Generate a Trust Card from accumulated predictions.

    Returns the Trust Card as structured JSON with confidence buckets,
    domain stats, danger zones, strength zones, and significance tests.
    """
    tracker = _get_tracker(agent)
    if not tracker.verified:
        return {"error": "No verified predictions yet."}

    card = tracker.generate_card()
    return card.to_dict()


@server.tool()
def caliber_summary(agent: str = DEFAULT_AGENT) -> str:
    """Quick calibration stats without a full Trust Card."""
    tracker = _get_tracker(agent)
    total = len(tracker.predictions)
    verified = len(tracker.verified)
    unverified = len(tracker.unverified)

    lines = [f"Agent: {agent}", f"Predictions: {total}"]
    if verified:
        correct = sum(1 for p in tracker.verified if p.outcome)
        lines.append(f"Verified: {verified} ({correct}/{verified} = {correct/verified:.1%})")
    if unverified:
        lines.append(f"Unverified: {unverified}")
    return "\n".join(lines)


@server.tool()
def caliber_list(
    agent: str = DEFAULT_AGENT,
    unverified_only: bool = False,
    domain: str = "",
) -> list[dict]:
    """List predictions.

    Args:
        agent: Agent name.
        unverified_only: Only show pending predictions.
        domain: Filter by domain (empty = all).
    """
    tracker = _get_tracker(agent)
    preds = tracker.unverified if unverified_only else tracker.predictions
    if domain:
        preds = [p for p in preds if p.domain == domain]

    return [
        {
            "id": p.id,
            "claim": p.claim,
            "confidence": p.confidence,
            "domain": p.domain,
            "outcome": p.outcome,
        }
        for p in preds
    ]


if __name__ == "__main__":
    server.run()
