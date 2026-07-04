"""Executable golden vectors for docs/SPEC.md."""

from __future__ import annotations

import json
from pathlib import Path

from caliber.event_log import EventLog
from caliber.storage import FileStorage
from caliber.tracker import TrustTracker


VECTORS = Path(__file__).parent / "vectors"


def _manifest() -> dict:
    return json.loads((VECTORS / "manifest.json").read_text())


def _without_generated(value):
    if isinstance(value, dict):
        return {
            key: _without_generated(item)
            for key, item in value.items()
            if key != "generated"
        }
    if isinstance(value, list):
        return [_without_generated(item) for item in value]
    return value


def test_valid_event_log_vector_head_matches_manifest():
    manifest = _manifest()
    agent = manifest["agent_name"]
    valid = manifest["valid_log"]
    directory = VECTORS / Path(valid["path"]).parent

    verification = EventLog(directory).verify(agent)

    assert verification.valid is True
    assert verification.event_count == valid["event_count"]
    assert verification.head_hash == valid["expected_head"]


def test_tampered_event_log_vector_fails_as_specified():
    manifest = _manifest()
    agent = manifest["agent_name"]
    tampered = manifest["tampered_log"]
    directory = VECTORS / Path(tampered["path"]).parent

    verification = EventLog(directory).verify(agent)

    assert verification.valid is tampered["expected_valid"]
    assert verification.error == tampered["expected_failure"]
    assert verification.failed_line == tampered["expected_failed_line"]


def test_structural_event_log_vector_fails_as_specified():
    manifest = _manifest()
    agent = manifest["agent_name"]
    structural = manifest["structural_log"]
    directory = VECTORS / Path(structural["path"]).parent

    verification = EventLog(directory).verify(agent)

    assert verification.valid is structural["expected_valid"]
    assert verification.error == structural["expected_failure"]
    assert verification.failed_line == structural["expected_failed_line"]


def test_card_vector_matches_event_log_backed_store():
    manifest = _manifest()
    agent = manifest["agent_name"]
    card_meta = manifest["card"]
    store_dir = VECTORS / card_meta["store_dir"]

    verification = EventLog(store_dir).verify(agent)
    tracker = TrustTracker(agent, storage=FileStorage(store_dir))
    recomputed = tracker.generate_card().to_dict()
    saved = json.loads((VECTORS / card_meta["path"]).read_text())

    assert verification.valid is True
    assert verification.event_count == card_meta["event_count"]
    assert verification.head_hash == card_meta["expected_head"]
    assert _without_generated(recomputed) == _without_generated(saved)
