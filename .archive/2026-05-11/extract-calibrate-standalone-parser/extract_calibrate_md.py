"""Extract predictions from MY UNIVERSE's CALIBRATE.md and generate
the first real Trust Card.

This is caliber's proof of concept — real data from real calibration work.
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from caliber import TrustTracker

CALIBRATE_MD = Path.home() / "MY UNIVERSE" / "CALIBRATE.md"


def parse_calibrate_md(path: Path) -> list[dict]:
    """Parse CALIBRATE.md entries into structured data."""
    text = path.read_text()
    entries = []

    # Split on entry headers: ### [P-NNN] YYYY-MM-DD — domain
    pattern = r"### \[P-(\d+)\] (\d{4}-\d{2}-\d{2}) — (\w+)\n\n(.*?)(?=\n### \[P-|\n---|\Z)"
    matches = re.finditer(pattern, text, re.DOTALL)

    for m in matches:
        pid = f"P-{m.group(1)}"
        date_str = m.group(2)
        domain = m.group(3)
        body = m.group(4).strip()

        # Extract fields
        claim_match = re.search(r"\*\*Prediction:\*\* (.+?)(?:\n|$)", body)
        conf_match = re.search(r"\*\*Confidence:\*\* (\d+)%", body)
        result_match = re.search(r"\*\*Result:\*\* (correct|incorrect|_pending_)", body)
        notes_match = re.search(r"\*\*Notes:\*\* (.+?)(?:\n\n|\Z)", body, re.DOTALL)

        if not all([claim_match, conf_match, result_match]):
            print(f"  Skipping {pid}: missing fields", file=sys.stderr)
            continue

        result = result_match.group(1)
        if result == "_pending_":
            print(f"  Skipping {pid}: pending verification", file=sys.stderr)
            continue

        entries.append({
            "id": pid,
            "date": date_str,
            "domain": domain,
            "claim": claim_match.group(1).strip(),
            "confidence": int(conf_match.group(1)) / 100,
            "correct": result == "correct",
            "notes": notes_match.group(1).strip() if notes_match else None,
        })

    return entries


def main():
    print(f"Reading: {CALIBRATE_MD}")
    entries = parse_calibrate_md(CALIBRATE_MD)
    print(f"Parsed: {len(entries)} verified predictions\n")

    # Create tracker and import all predictions
    tracker = TrustTracker("claude-opus-my-universe")

    for entry in entries:
        ts = datetime.strptime(entry["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        tracker.add_completed(
            claim=entry["claim"],
            confidence=entry["confidence"],
            domain=entry["domain"],
            correct=entry["correct"],
            timestamp=ts,
            notes=entry["notes"],
            prediction_id=entry["id"],
        )

    # Generate Trust Card
    card = tracker.generate_card()

    print("=" * 60)
    print(card.summary())
    print("=" * 60)
    print()

    # Save Trust Card JSON
    output_path = Path(__file__).parent / "trust-card-claude-opus.json"
    output_path.write_text(card.to_json() + "\n")
    print(f"Trust Card saved: {output_path}")

    # Also print raw JSON
    print(f"\n{card.to_json()}")


if __name__ == "__main__":
    main()
