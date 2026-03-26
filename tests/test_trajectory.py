"""Tests for caliber.trajectory."""

import pytest
from datetime import datetime, timezone, timedelta

from caliber.tracker import Prediction
from caliber.trajectory import Trajectory, Snapshot, Trend, _trend


def _make_preds(specs):
    """Make predictions from (confidence, domain, correct, day_offset) tuples."""
    preds = []
    base = datetime(2026, 3, 1, tzinfo=timezone.utc)
    for i, spec in enumerate(specs):
        if len(spec) == 4:
            conf, domain, correct, day = spec
        else:
            conf, domain, correct = spec
            day = i
        preds.append(Prediction(
            id=f"P-{i+1:03d}",
            claim=f"pred {i+1}",
            confidence=conf,
            domain=domain,
            timestamp=base + timedelta(days=day),
            outcome=correct,
            verified_at=base + timedelta(days=day),
        ))
    return preds


class TestTrajectory:
    def test_empty(self):
        traj = Trajectory.from_predictions("test", [])
        assert traj.snapshots == []

    def test_single_interval(self):
        preds = _make_preds([(0.80, "x", True)] * 10)
        traj = Trajectory.from_predictions("test", preds, interval=10)
        assert len(traj.snapshots) == 1

    def test_multiple_intervals(self):
        preds = _make_preds([(0.80, "x", True)] * 25)
        traj = Trajectory.from_predictions("test", preds, interval=10)
        # 10, 20, 25 (remainder)
        assert len(traj.snapshots) == 3

    def test_accuracy_trend_improving(self):
        # First 10: 60% accuracy. Last 10: 90% accuracy.
        early = [(0.80, "x", i < 6) for i in range(10)]
        late = [(0.80, "x", i < 9) for i in range(10)]
        preds = _make_preds(early + late)
        traj = Trajectory.from_predictions("test", preds, interval=10)
        acc_trend = next(t for t in traj.trends if t.metric == "overall_accuracy")
        assert acc_trend.direction == "improving"

    def test_accuracy_trend_stable(self):
        preds = _make_preds([(0.80, "x", True)] * 20)
        traj = Trajectory.from_predictions("test", preds, interval=10)
        acc_trend = next(t for t in traj.trends if t.metric == "overall_accuracy")
        assert acc_trend.direction == "stable"

    def test_summary_output(self):
        preds = _make_preds([(0.80, "x", True)] * 20)
        traj = Trajectory.from_predictions("test", preds, interval=10)
        summary = traj.summary()
        assert "test" in summary
        assert "Snapshots" in summary

    def test_to_dict(self):
        preds = _make_preds([(0.80, "x", True)] * 20)
        traj = Trajectory.from_predictions("test", preds, interval=10)
        d = traj.to_dict()
        assert d["agent_name"] == "test"
        assert len(d["snapshots"]) == 2
        assert "trends" in d


class TestTrendHelper:
    def test_improving(self):
        t = _trend("acc", 0.60, 0.80)
        assert t.direction == "improving"

    def test_declining(self):
        t = _trend("acc", 0.80, 0.60)
        assert t.direction == "declining"

    def test_stable(self):
        t = _trend("acc", 0.75, 0.77)
        assert t.direction == "stable"

    def test_insufficient(self):
        t = _trend("acc", None, 0.80)
        assert t.direction == "insufficient"
