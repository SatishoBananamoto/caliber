"""Tests for the append-only hash-chained event log."""

import json
from datetime import datetime, timezone

import pytest

from caliber.event_log import EventLog, GENESIS_HASH


T0 = datetime(2026, 7, 4, 12, 0, tzinfo=timezone.utc)


def _append_three(log: EventLog, agent: str = "agent") -> str:
    log.append(
        agent,
        "predicted",
        {"prediction_id": "p1", "claim": "first"},
        event_id="e1",
        created_at=T0,
    )
    log.append(
        agent,
        "verified",
        {"prediction_id": "p1", "correct": True},
        event_id="e2",
        created_at=T0,
    )
    third = log.append(
        agent,
        "imported",
        {"prediction_id": "p2", "origin": "fixture"},
        event_id="e3",
        created_at=T0,
    )
    return third.line_hash


def test_path_for_uses_url_safe_agent_name(tmp_path):
    log = EventLog(tmp_path)

    assert log.path_for("agent alpha/v2") == tmp_path / "agent%20alpha%2Fv2.events.jsonl"


def test_append_replay_and_verify_chain(tmp_path):
    log = EventLog(tmp_path)

    first = log.append(
        "agent",
        "predicted",
        {"prediction_id": "p1", "claim": "first"},
        event_id="e1",
        created_at=T0,
    )
    second = log.append(
        "agent",
        "verified",
        {"prediction_id": "p1", "correct": True},
        event_id="e2",
        created_at=T0,
    )

    events = log.replay("agent")
    verification = log.verify("agent")

    assert [event["type"] for event in events] == ["predicted", "verified"]
    assert events[0]["prev_hash"] == GENESIS_HASH
    assert events[1]["prev_hash"] == first.line_hash
    assert verification.valid is True
    assert verification.event_count == 2
    assert verification.head_hash == second.line_hash


def test_middle_line_mutation_breaks_next_prev_hash(tmp_path):
    log = EventLog(tmp_path)
    _append_three(log)
    path = log.path_for("agent")

    lines = path.read_bytes().splitlines()
    event = json.loads(lines[1])
    event["payload"]["correct"] = False
    lines[1] = json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
    path.write_bytes(b"\n".join(lines) + b"\n")

    verification = log.verify("agent")

    assert verification.valid is False
    assert verification.failed_line == 3
    assert verification.error == "prev_hash does not match previous line hash"


def test_deleted_line_breaks_chain(tmp_path):
    log = EventLog(tmp_path)
    _append_three(log)
    path = log.path_for("agent")

    lines = path.read_bytes().splitlines()
    path.write_bytes(b"\n".join([lines[0], lines[2]]) + b"\n")

    verification = log.verify("agent")

    assert verification.valid is False
    assert verification.failed_line == 2
    assert verification.error == "prev_hash does not match previous line hash"


def test_reordered_lines_break_chain(tmp_path):
    log = EventLog(tmp_path)
    _append_three(log)
    path = log.path_for("agent")

    lines = path.read_bytes().splitlines()
    path.write_bytes(b"\n".join([lines[1], lines[0], lines[2]]) + b"\n")

    verification = log.verify("agent")

    assert verification.valid is False
    assert verification.failed_line == 1
    assert verification.error == "prev_hash does not match previous line hash"


def test_expected_head_catches_last_line_edit(tmp_path):
    log = EventLog(tmp_path)
    expected_head = _append_three(log)
    path = log.path_for("agent")

    lines = path.read_bytes().splitlines()
    event = json.loads(lines[-1])
    event["payload"]["origin"] = "tampered"
    lines[-1] = json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
    path.write_bytes(b"\n".join(lines) + b"\n")

    unanchored = log.verify("agent")
    anchored = log.verify("agent", expected_head=expected_head)

    assert unanchored.valid is True
    assert unanchored.head_hash != expected_head
    assert anchored.valid is False
    assert anchored.error == "head hash does not match expected_head"


def test_replay_rejects_invalid_log(tmp_path):
    log = EventLog(tmp_path)
    _append_three(log)
    path = log.path_for("agent")
    path.write_bytes(b"not json\n")

    with pytest.raises(ValueError, match="invalid log"):
        log.replay("agent")
