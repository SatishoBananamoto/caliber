"""Persistence for caliber predictions.

v0.1: flat JSON files. One file per agent.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

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

    def _path_for(self, agent_name: str) -> Path:
        safe_name = agent_name.replace("/", "_").replace(" ", "_")
        return self.directory / f"{safe_name}.json"

    def save(self, agent_name: str, predictions: list[Prediction]) -> None:
        path = self._path_for(agent_name)
        data = {
            "agent_name": agent_name,
            "predictions": [p.to_dict() for p in predictions],
        }
        path.write_text(json.dumps(data, indent=2) + "\n")

    def load(self, agent_name: str) -> list[Prediction]:
        from caliber.tracker import Prediction

        path = self._path_for(agent_name)
        if not path.exists():
            return []
        data = json.loads(path.read_text())
        return [Prediction.from_dict(p) for p in data["predictions"]]


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
