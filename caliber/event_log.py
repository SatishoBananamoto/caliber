"""Append-only hash-chained JSONL event logs.

This module is the Phase 3 tamper-evidence primitive. It does not replace
``FileStorage`` by itself; storage integration happens after the chain mechanics
are independently tested.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote


GENESIS_HASH = "0" * 64
LOG_VERSION = 1


@dataclass(frozen=True)
class EventAppendResult:
    """Result of appending one event to an event log."""

    path: Path
    event: dict[str, Any]
    line_hash: str


@dataclass(frozen=True)
class LogVerification:
    """Structural verification result for one event log."""

    path: Path
    valid: bool
    event_count: int
    head_hash: str
    error: str | None = None
    failed_line: int | None = None


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"{type(value).__name__} is not JSON serializable")


def _canonical_line(event: dict[str, Any]) -> bytes:
    return json.dumps(
        event,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    ).encode("utf-8")


def _hash_line(line: bytes) -> str:
    return hashlib.sha256(line).hexdigest()


class EventLog:
    """Append and verify hash-chained event logs for one storage directory."""

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def path_for(self, agent_name: str) -> Path:
        safe_name = quote(agent_name, safe="")
        return self.directory / f"{safe_name}.events.jsonl"

    def append(
        self,
        agent_name: str,
        event_type: str,
        payload: dict[str, Any],
        *,
        event_id: str | None = None,
        created_at: datetime | None = None,
    ) -> EventAppendResult:
        if not event_type:
            raise ValueError("event_type must be non-empty")

        path = self.path_for(agent_name)
        verification = self.verify(agent_name)
        if not verification.valid:
            raise ValueError(f"cannot append to invalid log: {verification.error}")

        event = {
            "version": LOG_VERSION,
            "type": event_type,
            "event_id": event_id or uuid.uuid4().hex,
            "agent_name": agent_name,
            "created_at": (created_at or datetime.now(timezone.utc)).isoformat(),
            "prev_hash": verification.head_hash,
            "payload": payload,
        }
        line = _canonical_line(event)
        with path.open("ab") as f:
            f.write(line + b"\n")
        return EventAppendResult(path=path, event=event, line_hash=_hash_line(line))

    def replay(self, agent_name: str) -> list[dict[str, Any]]:
        verification = self.verify(agent_name)
        if not verification.valid:
            raise ValueError(f"invalid log: {verification.error}")

        path = self.path_for(agent_name)
        if not path.exists():
            return []
        return [
            json.loads(line.decode("utf-8"))
            for line in path.read_bytes().splitlines()
        ]

    def verify(
        self,
        agent_name: str,
        *,
        expected_head: str | None = None,
    ) -> LogVerification:
        path = self.path_for(agent_name)
        if not path.exists():
            head_hash = GENESIS_HASH
            if expected_head is not None and expected_head != head_hash:
                return LogVerification(
                    path=path,
                    valid=False,
                    event_count=0,
                    head_hash=head_hash,
                    error="head hash does not match expected_head",
                )
            return LogVerification(path, True, 0, head_hash)

        previous_hash = GENESIS_HASH
        raw_lines = path.read_bytes().splitlines()
        for line_number, line in enumerate(raw_lines, start=1):
            if not line:
                return LogVerification(
                    path=path,
                    valid=False,
                    event_count=line_number - 1,
                    head_hash=previous_hash,
                    error="empty line in event log",
                    failed_line=line_number,
                )

            try:
                event = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                return LogVerification(
                    path=path,
                    valid=False,
                    event_count=line_number - 1,
                    head_hash=previous_hash,
                    error=f"invalid JSON: {exc}",
                    failed_line=line_number,
                )

            observed_prev = event.get("prev_hash")
            if observed_prev != previous_hash:
                return LogVerification(
                    path=path,
                    valid=False,
                    event_count=line_number - 1,
                    head_hash=previous_hash,
                    error="prev_hash does not match previous line hash",
                    failed_line=line_number,
                )

            previous_hash = _hash_line(line)

        if expected_head is not None and expected_head != previous_hash:
            return LogVerification(
                path=path,
                valid=False,
                event_count=len(raw_lines),
                head_hash=previous_hash,
                error="head hash does not match expected_head",
            )

        return LogVerification(
            path=path,
            valid=True,
            event_count=len(raw_lines),
            head_hash=previous_hash,
        )
