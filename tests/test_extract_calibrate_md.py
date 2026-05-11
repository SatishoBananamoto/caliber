"""Tests for the MY UNIVERSE Trust Card compatibility wrapper."""

import json

from extract_calibrate_md import build_trust_card


SAMPLE_CALIBRATE_MD = """\
# CALIBRATE.md

### [P-001] 2026-03-24 — codebase

**Prediction:** Project has fewer than 15 files.
**Confidence:** 75%
**Actual:** 10 files.
**Result:** correct
**Notes:** Test note.

### [P-002] 2026-03-24 — architecture

**Prediction:** Uses asyncio.
**Confidence:** 70%
**Actual:** No asyncio found.
**Result:** incorrect

### [P-003] 2026-03-24 — facts

**Prediction:** Something pending.
**Confidence:** 60%
**Actual:** _to be verified_
**Result:** _pending_
"""


def test_build_trust_card_uses_shared_importer(tmp_path):
    source = tmp_path / "CALIBRATE.md"
    output = tmp_path / "trust-card.json"
    source.write_text(SAMPLE_CALIBRATE_MD)

    count, card = build_trust_card(source, output, agent_name="test-agent")

    assert count == 2
    assert card.agent_name == "test-agent"
    assert card.total_verified == 2

    data = json.loads(output.read_text())
    assert data["agent_name"] == "test-agent"
    assert data["calibration"]["total_verified"] == 2
