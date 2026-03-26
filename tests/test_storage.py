"""Tests for caliber.storage."""

import json
import tempfile
import pytest
from datetime import datetime, timezone
from pathlib import Path

from caliber.tracker import Prediction
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
        assert (tmp_path / "my_agent_v2.json").exists()

    def test_overwrite(self, tmp_path):
        s = FileStorage(tmp_path)
        s.save("agent", [_make_prediction("p1")])
        s.save("agent", [_make_prediction("p1"), _make_prediction("p2")])
        loaded = s.load("agent")
        assert len(loaded) == 2
