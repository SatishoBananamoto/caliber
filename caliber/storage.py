"""Persistence for caliber predictions.

v0.1: flat JSON files. One file per agent.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import quote

from caliber.event_log import EventLog

if TYPE_CHECKING:
    from caliber.tracker import Prediction


class Storage(ABC):
    """Abstract storage backend."""

    @abstractmethod
    def save(self, agent_name: str, predictions: list[Prediction]) -> None: ...

    @abstractmethod
    def load(self, agent_name: str) -> list[Prediction]: ...


class FileStorage(Storage):
    """Store predictions as JSON files, one per agent."""

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self._event_log = EventLog(self.directory)

    def _path_for(self, agent_name: str) -> Path:
        safe_name = quote(agent_name, safe="")
        return self.directory / f"{safe_name}.json"

    def _legacy_path_for(self, agent_name: str) -> Path:
        safe_name = agent_name.replace("/", "_").replace(" ", "_")
        return self.directory / f"{safe_name}.json"

    def migrate_snapshot(self, agent_name: str) -> dict:
        """Convert a legacy JSON snapshot into an unwitnessed event log.

        Migration marks every existing prediction as ``imported`` with
        ``origin: migrated``. This is honest: the chain proves future ordering,
        not that pre-migration events were witnessed when they happened.
        """
        event_path = self._event_log.path_for(agent_name)
        if event_path.exists():
            raise ValueError(f"event log already exists: {event_path}")

        snapshot_path = self._path_for(agent_name)
        legacy_path = self._legacy_path_for(agent_name)
        if not snapshot_path.exists() and not legacy_path.exists():
            raise FileNotFoundError(f"no JSON snapshot found for {agent_name!r}")

        predictions = self._load_from_snapshot(agent_name)
        if not predictions:
            event_path.touch()
        for prediction in predictions:
            self._event_log.append(
                agent_name,
                "imported",
                {
                    "origin": "migrated",
                    "prediction": prediction.to_dict(),
                },
            )

        # Rewrite the canonical JSON snapshot as a derived cache.
        self.save(agent_name, predictions)
        verification = self._event_log.verify(agent_name)
        return {
            "agent_name": agent_name,
            "snapshot_path": str(snapshot_path if snapshot_path.exists() else legacy_path),
            "event_log_path": str(event_path),
            "migrated_count": len(predictions),
            "head_hash": verification.head_hash,
        }

    def save(self, agent_name: str, predictions: list[Prediction]) -> None:
        self._append_events_for_delta(agent_name, predictions)
        path = self._path_for(agent_name)
        data = {
            "agent_name": agent_name,
            "predictions": [p.to_dict() for p in predictions],
        }
        path.write_text(json.dumps(data, indent=2) + "\n")

    def load(self, agent_name: str) -> list[Prediction]:
        event_path = self._event_log.path_for(agent_name)
        if event_path.exists():
            return self._load_from_events(agent_name)
        return self._load_from_snapshot(agent_name)

    def _load_from_snapshot(self, agent_name: str) -> list[Prediction]:
        from caliber.tracker import Prediction

        path = self._path_for(agent_name)
        if not path.exists():
            legacy_path = self._legacy_path_for(agent_name)
            if legacy_path.exists():
                path = legacy_path
        if not path.exists():
            return []
        data = json.loads(path.read_text())
        return [Prediction.from_dict(p) for p in data["predictions"]]

    def _load_from_events(self, agent_name: str) -> list[Prediction]:
        from caliber.tracker import Prediction

        predictions: dict[str, Prediction] = {}
        for event in self._event_log.replay(agent_name):
            event_type = event["type"]
            payload = event["payload"]
            if event_type in {"predicted", "imported"}:
                prediction = Prediction.from_dict(payload["prediction"])
                predictions[prediction.id] = prediction
            elif event_type == "anchor":
                continue
            elif event_type == "verified":
                prediction_id = payload["prediction_id"]
                if prediction_id not in predictions:
                    raise ValueError(
                        f"invalid event log: verify before predict for {prediction_id}"
                    )
                prediction = predictions[prediction_id]
                prediction.outcome = payload["outcome"]
                prediction.verified_at = (
                    _datetime_from_iso(payload["verified_at"])
                    if payload.get("verified_at")
                    else None
                )
                prediction.notes = payload.get("notes")
            elif event_type == "adjudicated":
                prediction_id = payload["prediction_id"]
                if prediction_id not in predictions:
                    raise ValueError(
                        f"invalid event log: adjudicate before predict for {prediction_id}"
                    )
                prediction = predictions[prediction_id]
                adjudicated_at = (
                    _datetime_from_iso(payload["adjudicated_at"])
                    if payload.get("adjudicated_at")
                    else None
                )
                prediction.outcome = payload["outcome"]
                prediction.verified_at = adjudicated_at
                prediction.notes = payload.get("evidence_note")
                prediction.adjudicated_by = payload["adjudicator"]
                prediction.adjudicated_at = adjudicated_at
                prediction.adjudication_note = payload.get("evidence_note")
                prediction.adjudicator_signature = payload.get(
                    "adjudicator_signature"
                )
            else:
                raise ValueError(f"invalid event log: unknown event type {event_type!r}")
        return list(predictions.values())

    def _append_events_for_delta(
        self,
        agent_name: str,
        predictions: list[Prediction],
    ) -> None:
        event_path = self._event_log.path_for(agent_name)
        snapshot_path = self._path_for(agent_name)
        legacy_event_log = (
            not event_path.exists()
            and (snapshot_path.exists() or self._legacy_path_for(agent_name).exists())
        )
        if legacy_event_log:
            # Explicit migration is a separate Phase 3 command. Until then,
            # JSON-only stores remain JSON-only instead of getting a partial log.
            return

        previous = {p.id: p for p in self.load(agent_name)}
        for prediction in predictions:
            prior = previous.get(prediction.id)
            if prior is None:
                event_type = "imported" if prediction.outcome is not None else "predicted"
                self._event_log.append(
                    agent_name,
                    event_type,
                    {"prediction": prediction.to_dict()},
                )
            elif _verification_changed(prior, prediction):
                if prediction.adjudicated_by:
                    self._event_log.append(
                        agent_name,
                        "adjudicated",
                        {
                            "prediction_id": prediction.id,
                            "outcome": prediction.outcome,
                            "adjudicated_at": (
                                prediction.adjudicated_at.isoformat()
                                if prediction.adjudicated_at
                                else None
                            ),
                            "adjudicator": prediction.adjudicated_by,
                            "evidence_note": prediction.adjudication_note,
                            "adjudicator_signature": (
                                prediction.adjudicator_signature
                            ),
                        },
                    )
                else:
                    self._event_log.append(
                        agent_name,
                        "verified",
                        {
                            "prediction_id": prediction.id,
                            "outcome": prediction.outcome,
                            "verified_at": (
                                prediction.verified_at.isoformat()
                                if prediction.verified_at
                                else None
                            ),
                            "notes": prediction.notes,
                        },
                    )


def _datetime_from_iso(value: str):
    from datetime import datetime

    return datetime.fromisoformat(value)


def _verification_changed(before: Prediction, after: Prediction) -> bool:
    return (
        before.outcome != after.outcome
        or before.verified_at != after.verified_at
        or before.notes != after.notes
        or before.adjudicated_by != after.adjudicated_by
        or before.adjudicated_at != after.adjudicated_at
        or before.adjudication_note != after.adjudication_note
        or before.adjudicator_signature != after.adjudicator_signature
    )


class MemoryStorage(Storage):
    """In-memory storage for testing."""

    def __init__(self):
        self._store: dict[str, list[dict]] = {}

    def save(self, agent_name: str, predictions: list[Prediction]) -> None:
        self._store[agent_name] = [p.to_dict() for p in predictions]

    def load(self, agent_name: str) -> list[Prediction]:
        from caliber.tracker import Prediction

        if agent_name not in self._store:
            return []
        return [Prediction.from_dict(p) for p in self._store[agent_name]]
