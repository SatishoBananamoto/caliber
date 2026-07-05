"""Tests for caliber.storage."""

import json
import tempfile
import pytest
from datetime import datetime, timezone
from pathlib import Path

from caliber.tracker import Prediction, TrustTracker
from caliber.storage import FileStorage, MemoryStorage


def _make_prediction(pid="test-1", outcome=True):
    return Prediction(
        id=pid,
        claim="test claim",
        confidence=0.80,
        domain="test",
        timestamp=datetime(2026, 3, 24, tzinfo=timezone.utc),
        outcome=outcome,
        verified_at=datetime(2026, 3, 24, 0, 1, tzinfo=timezone.utc),
    )


class TestMemoryStorage:
    def test_save_and_load(self):
        s = MemoryStorage()
        preds = [_make_prediction("p1"), _make_prediction("p2")]
        s.save("agent-a", preds)
        loaded = s.load("agent-a")
        assert len(loaded) == 2
        assert loaded[0].id == "p1"

    def test_load_nonexistent(self):
        s = MemoryStorage()
        assert s.load("ghost") == []

    def test_isolation(self):
        s = MemoryStorage()
        s.save("agent-a", [_make_prediction("p1")])
        s.save("agent-b", [_make_prediction("p2")])
        assert len(s.load("agent-a")) == 1
        assert s.load("agent-a")[0].id == "p1"


class TestFileStorage:
    def test_save_and_load(self, tmp_path):
        s = FileStorage(tmp_path)
        preds = [_make_prediction("p1"), _make_prediction("p2", outcome=False)]
        s.save("my-agent", preds)
        loaded = s.load("my-agent")
        assert len(loaded) == 2
        assert loaded[0].id == "p1"
        assert loaded[1].outcome is False

    def test_load_nonexistent(self, tmp_path):
        s = FileStorage(tmp_path)
        assert s.load("ghost") == []

    def test_file_created(self, tmp_path):
        s = FileStorage(tmp_path)
        s.save("agent-x", [_make_prediction()])
        assert (tmp_path / "agent-x.json").exists()

    def test_file_is_valid_json(self, tmp_path):
        s = FileStorage(tmp_path)
        s.save("agent-x", [_make_prediction()])
        data = json.loads((tmp_path / "agent-x.json").read_text())
        assert data["agent_name"] == "agent-x"
        assert len(data["predictions"]) == 1

    def test_creates_directory(self, tmp_path):
        nested = tmp_path / "deep" / "path"
        s = FileStorage(nested)
        s.save("agent", [_make_prediction()])
        assert nested.exists()

    def test_sanitizes_name(self, tmp_path):
        s = FileStorage(tmp_path)
        s.save("my agent/v2", [_make_prediction()])
        assert (tmp_path / "my%20agent%2Fv2.json").exists()

    def test_distinguishes_collision_prone_agent_names(self, tmp_path):
        s = FileStorage(tmp_path)
        s.save("my agent/v2", [_make_prediction("space-slash")])
        s.save("my_agent_v2", [_make_prediction("underscore")])

        assert s.load("my agent/v2")[0].id == "space-slash"
        assert s.load("my_agent_v2")[0].id == "underscore"

    def test_loads_legacy_sanitized_name(self, tmp_path):
        legacy_path = tmp_path / "my_agent_v2.json"
        legacy_path.write_text(json.dumps({
            "agent_name": "my agent/v2",
            "predictions": [_make_prediction("legacy").to_dict()],
        }))

        s = FileStorage(tmp_path)
        assert s.load("my agent/v2")[0].id == "legacy"

    def test_overwrite(self, tmp_path):
        s = FileStorage(tmp_path)
        s.save("agent", [_make_prediction("p1")])
        s.save("agent", [_make_prediction("p1"), _make_prediction("p2")])
        loaded = s.load("agent")
        assert len(loaded) == 2

    def test_new_store_writes_event_log_and_replays_over_snapshot(self, tmp_path):
        s = FileStorage(tmp_path)
        tracker = TrustTracker("agent", storage=s)
        pid = tracker.predict(
            "event log claim",
            confidence=0.80,
            domain="test",
            timestamp=datetime(2026, 3, 24, tzinfo=timezone.utc),
            prediction_id="p1",
        )
        tracker.verify(
            pid,
            correct=True,
            verified_at=datetime(2026, 3, 24, 0, 2, tzinfo=timezone.utc),
        )

        event_path = tmp_path / "agent.events.jsonl"
        assert event_path.exists()
        events = [json.loads(line) for line in event_path.read_text().splitlines()]
        assert [event["type"] for event in events] == ["predicted", "verified"]

        snapshot = json.loads((tmp_path / "agent.json").read_text())
        snapshot["predictions"][0]["outcome"] = False
        (tmp_path / "agent.json").write_text(json.dumps(snapshot) + "\n")

        loaded = FileStorage(tmp_path).load("agent")
        assert loaded[0].outcome is True

    def test_add_completed_creates_imported_event_for_new_store(self, tmp_path):
        tracker = TrustTracker("agent", storage=FileStorage(tmp_path))
        tracker.add_completed(
            "historical claim",
            confidence=0.70,
            domain="history",
            correct=False,
            timestamp=datetime(2026, 3, 24, tzinfo=timezone.utc),
            prediction_id="p1",
        )

        event_path = tmp_path / "agent.events.jsonl"
        event = json.loads(event_path.read_text().splitlines()[0])

        assert event["type"] == "imported"
        loaded = FileStorage(tmp_path).load("agent")
        assert loaded[0].id == "p1"
        assert loaded[0].outcome is False

    def test_adjudication_writes_adjudicated_event_for_new_store(self, tmp_path):
        tracker = TrustTracker("agent", storage=FileStorage(tmp_path))
        tracker.predict(
            "external claim",
            confidence=0.80,
            domain="facts",
            timestamp=datetime(2026, 3, 24, tzinfo=timezone.utc),
            prediction_id="p1",
        )
        tracker.adjudicate(
            "p1",
            correct=False,
            adjudicator="reviewer@example.com",
            evidence_note="evidence note",
            adjudicator_signature="sig-1",
            adjudicated_at=datetime(2026, 3, 25, tzinfo=timezone.utc),
        )

        event_path = tmp_path / "agent.events.jsonl"
        events = [json.loads(line) for line in event_path.read_text().splitlines()]
        assert [event["type"] for event in events] == ["predicted", "adjudicated"]
        payload = events[1]["payload"]
        assert payload["prediction_id"] == "p1"
        assert payload["outcome"] is False
        assert payload["adjudicator"] == "reviewer@example.com"
        assert payload["evidence_note"] == "evidence note"
        assert payload["adjudicator_signature"] == "sig-1"

        loaded = FileStorage(tmp_path).load("agent")[0]
        assert loaded.outcome is False
        assert loaded.adjudicated_by == "reviewer@example.com"
        assert loaded.adjudication_note == "evidence note"
        assert loaded.adjudicator_signature == "sig-1"

    def test_invalid_event_log_fails_loudly(self, tmp_path):
        tracker = TrustTracker("agent", storage=FileStorage(tmp_path))
        pid = tracker.predict(
            "event log claim",
            confidence=0.80,
            domain="test",
            prediction_id="p1",
        )
        tracker.verify(pid, correct=True)

        event_path = tmp_path / "agent.events.jsonl"
        lines = event_path.read_text().splitlines()
        event = json.loads(lines[0])
        event["payload"]["prediction"]["claim"] = "tampered"
        lines[0] = json.dumps(event, sort_keys=True, separators=(",", ":"))
        event_path.write_text("\n".join(lines) + "\n")

        with pytest.raises(ValueError, match="invalid log"):
            FileStorage(tmp_path).load("agent")

    def test_legacy_json_store_does_not_auto_create_partial_event_log(self, tmp_path):
        legacy_path = tmp_path / "my_agent.json"
        legacy_path.write_text(json.dumps({
            "agent_name": "my agent",
            "predictions": [_make_prediction("legacy").to_dict()],
        }) + "\n")

        s = FileStorage(tmp_path)
        predictions = s.load("my agent")
        predictions.append(_make_prediction("new"))
        s.save("my agent", predictions)

        assert not (tmp_path / "my%20agent.events.jsonl").exists()
        assert s.load("my agent")[0].id == "legacy"
