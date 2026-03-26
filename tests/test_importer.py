"""Tests for caliber.importer."""

import pytest
from pathlib import Path

from caliber.tracker import TrustTracker
from caliber.storage import MemoryStorage
from caliber.importer import import_calibrate_md, import_csv


SAMPLE_CALIBRATE_MD = """\
# CALIBRATE.md

## Entries

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

---
"""


class TestImportCalibrateMd:
    def test_basic_import(self, tmp_path):
        md_file = tmp_path / "CALIBRATE.md"
        md_file.write_text(SAMPLE_CALIBRATE_MD)

        tracker = TrustTracker("test", storage=MemoryStorage())
        count = import_calibrate_md(md_file, tracker)
        assert count == 2  # P-003 is pending, skipped
        assert len(tracker.verified) == 2

    def test_correct_values(self, tmp_path):
        md_file = tmp_path / "CALIBRATE.md"
        md_file.write_text(SAMPLE_CALIBRATE_MD)

        tracker = TrustTracker("test", storage=MemoryStorage())
        import_calibrate_md(md_file, tracker)

        p1 = tracker.get("P-001")
        assert p1.confidence == 0.75
        assert p1.domain == "codebase"
        assert p1.outcome is True

        p2 = tracker.get("P-002")
        assert p2.confidence == 0.70
        assert p2.outcome is False

    def test_skips_pending(self, tmp_path):
        md_file = tmp_path / "CALIBRATE.md"
        md_file.write_text(SAMPLE_CALIBRATE_MD)

        tracker = TrustTracker("test", storage=MemoryStorage())
        import_calibrate_md(md_file, tracker)
        with pytest.raises(KeyError):
            tracker.get("P-003")


SAMPLE_CSV = """\
claim,confidence,domain,correct,notes
sky is blue,90,facts,true,obvious
water is dry,70,facts,false,wrong
"""


class TestImportCsv:
    def test_basic_import(self, tmp_path):
        csv_file = tmp_path / "data.csv"
        csv_file.write_text(SAMPLE_CSV)

        tracker = TrustTracker("test", storage=MemoryStorage())
        count = import_csv(csv_file, tracker)
        assert count == 2

    def test_correct_values(self, tmp_path):
        csv_file = tmp_path / "data.csv"
        csv_file.write_text(SAMPLE_CSV)

        tracker = TrustTracker("test", storage=MemoryStorage())
        import_csv(csv_file, tracker)

        preds = tracker.verified
        assert len(preds) == 2
        correct_pred = [p for p in preds if p.outcome is True][0]
        assert correct_pred.confidence == 0.90
        assert correct_pred.domain == "facts"

    def test_percentage_confidence(self, tmp_path):
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("claim,confidence,domain,correct\ntest,85,x,yes\n")

        tracker = TrustTracker("test", storage=MemoryStorage())
        import_csv(csv_file, tracker)
        assert tracker.predictions[0].confidence == 0.85
