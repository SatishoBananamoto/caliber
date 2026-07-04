"""Compatibility wrapper for importing MY UNIVERSE calibration data.

The maintained import path is ``caliber import`` / ``caliber.importer``.
This script remains for the original proof-of-concept workflow: generate the
repo's sample Trust Card JSON from MY UNIVERSE's CALIBRATE.md.
"""

from pathlib import Path

from caliber import TrustTracker
from caliber.importer import import_calibrate_md
from caliber.storage import MemoryStorage

CALIBRATE_MD = Path.home() / "MY UNIVERSE" / "CALIBRATE.md"
DEFAULT_AGENT = "claude-opus-my-universe"
DEFAULT_OUTPUT = Path(__file__).parent / "trust-card-claude-opus.json"


def build_trust_card(
    input_path: Path = CALIBRATE_MD,
    output_path: Path = DEFAULT_OUTPUT,
    agent_name: str = DEFAULT_AGENT,
):
    """Import CALIBRATE.md through the shared importer and write a Trust Card."""
    tracker = TrustTracker(agent_name, storage=MemoryStorage())
    count = import_calibrate_md(input_path, tracker)
    card = tracker.generate_card()
    output_path.write_text(card.to_json() + "\n")
    return count, card


def main():
    print(f"Reading: {CALIBRATE_MD}")
    count, card = build_trust_card()
    print(f"Parsed: {count} verified predictions\n")

    print("=" * 60)
    print(card.summary())
    print("=" * 60)
    print()

    print(f"Trust Card saved: {DEFAULT_OUTPUT}")

    # Also print raw JSON
    print(f"\n{card.to_json()}")


if __name__ == "__main__":
    main()
