"""Import predictions from external formats into caliber.

Supports:
- CALIBRATE.md format (MY UNIVERSE)
- CSV format (claim,confidence,domain,correct,notes)
"""

from __future__ import annotations

import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from caliber.tracker import TrustTracker


def import_calibrate_md(
    path: Path | str,
    tracker: TrustTracker,
) -> int:
    """Import predictions from a CALIBRATE.md-format file.

    Returns the number of predictions imported.
    """
    text = Path(path).read_text()
    count = 0

    pattern = (
        r"### \[P-(\d+)\] (\d{4}-\d{2}-\d{2}) — (\w+)\s*\n+"
        r"(.*?)(?=\n### \[P-|\n---|\Z)"
    )
    for m in re.finditer(pattern, text, re.DOTALL):
        pid = f"P-{m.group(1)}"
        date_str = m.group(2)
        domain = m.group(3)
        body = m.group(4).strip()

        claim_match = re.search(r"\*\*Prediction:\*\* (.+?)(?:\n|$)", body)
        conf_match = re.search(r"\*\*Confidence:\*\* (\d+)%", body)
        result_match = re.search(
            r"\*\*Result:\*\* (correct|incorrect|_pending_)", body
        )
        notes_match = re.search(
            r"\*\*Notes:\*\* (.+?)(?:\n\n|\Z)", body, re.DOTALL
        )

        if not all([claim_match, conf_match, result_match]):
            continue

        result = result_match.group(1)
        if result == "_pending_":
            continue

        ts = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        tracker.add_completed(
            claim=claim_match.group(1).strip(),
            confidence=int(conf_match.group(1)) / 100,
            domain=domain,
            correct=(result == "correct"),
            timestamp=ts,
            notes=notes_match.group(1).strip() if notes_match else None,
            prediction_id=pid,
        )
        count += 1

    return count


def import_csv(
    path: Path | str,
    tracker: TrustTracker,
) -> int:
    """Import predictions from CSV.

    Expected columns: claim,confidence,domain,correct[,notes]
    Confidence can be 0.50-0.99 or 50-99.
    Correct should be "true"/"false"/"yes"/"no"/"1"/"0".
    """
    count = 0
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            conf = float(row["confidence"])
            if conf >= 1.0:
                conf /= 100

            correct_str = row["correct"].strip().lower()
            correct = correct_str in ("true", "yes", "1", "correct")

            tracker.add_completed(
                claim=row["claim"],
                confidence=conf,
                domain=row["domain"],
                correct=correct,
                notes=row.get("notes", "").strip() or None,
            )
            count += 1

    return count
