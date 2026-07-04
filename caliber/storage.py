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
