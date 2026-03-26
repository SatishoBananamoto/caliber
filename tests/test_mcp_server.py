"""Tests for caliber MCP server tools."""

import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from caliber.mcp_server import (
    caliber_predict,
    caliber_verify,
    caliber_card,
    caliber_summary,
    caliber_list,
    _trackers,
    _storage,
    _get_tracker,
)
from caliber.storage import FileStorage


@pytest.fixture(autouse=True)
def clean_trackers(tmp_path):
    """Reset tracker registry and use temp storage for each test."""
    import caliber.mcp_server as mod
    _trackers.clear()
    mod._storage = FileStorage(tmp_path)
    yield
    _trackers.clear()


class TestMCPTools:
    def test_predict_returns_id(self):
        result = caliber_predict("sky is blue", 85, "facts")
        assert "Prediction recorded:" in result

    def test_predict_accepts_percentage(self):
        result = caliber_predict("test", 80, "x")
        assert "80%" in result

    def test_predict_accepts_decimal(self):
        result = caliber_predict("test", 0.80, "x")
        assert "80%" in result

    def test_verify_correct(self):
        caliber_predict("test", 80, "x", prediction_id="test-1")
        result = caliber_verify("test-1", correct=True)
        assert "correct" in result

    def test_verify_incorrect(self):
        caliber_predict("test", 80, "x", prediction_id="test-2")
        result = caliber_verify("test-2", correct=False)
        assert "incorrect" in result

    def test_card_returns_dict(self):
        caliber_predict("a", 80, "x", prediction_id="p1")
        caliber_verify("p1", correct=True)
        card = caliber_card()
        assert isinstance(card, dict)
        assert card["agent_name"] == "default"
        assert "calibration" in card

    def test_card_empty_error(self):
        card = caliber_card()
        assert "error" in card

    def test_card_has_significance(self):
        # Add enough predictions for significance test
        for i in range(10):
            caliber_predict(f"pred {i}", 85, "test", prediction_id=f"sig-{i}")
            caliber_verify(f"sig-{i}", correct=(i < 8))
        card = caliber_card()
        buckets = card["calibration"]["confidence_buckets"]
        assert "80-89" in buckets
        assert "significant" in buckets["80-89"]

    def test_summary(self):
        caliber_predict("a", 80, "x", prediction_id="s1")
        caliber_verify("s1", correct=True)
        result = caliber_summary()
        assert "default" in result
        assert "100.0%" in result

    def test_list_all(self):
        caliber_predict("a", 80, "x", prediction_id="l1")
        caliber_predict("b", 70, "y", prediction_id="l2")
        result = caliber_list()
        assert len(result) == 2

    def test_list_unverified(self):
        caliber_predict("a", 80, "x", prediction_id="u1")
        caliber_predict("b", 70, "y", prediction_id="u2")
        caliber_verify("u1", correct=True)
        result = caliber_list(unverified_only=True)
        assert len(result) == 1
        assert result[0]["id"] == "u2"

    def test_list_by_domain(self):
        caliber_predict("a", 80, "security", prediction_id="d1")
        caliber_predict("b", 70, "style", prediction_id="d2")
        result = caliber_list(domain="security")
        assert len(result) == 1

    def test_multi_agent(self):
        caliber_predict("a", 80, "x", agent="agent-a", prediction_id="ma1")
        caliber_predict("b", 70, "x", agent="agent-b", prediction_id="mb1")
        caliber_verify("ma1", correct=True, agent="agent-a")
        caliber_verify("mb1", correct=False, agent="agent-b")

        card_a = caliber_card(agent="agent-a")
        card_b = caliber_card(agent="agent-b")
        assert card_a["calibration"]["overall_accuracy"] == 1.0
        assert card_b["calibration"]["overall_accuracy"] == 0.0
