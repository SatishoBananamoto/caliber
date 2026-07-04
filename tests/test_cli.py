"""Tests for caliber CLI commands."""

import json

from click.testing import CliRunner

from caliber.cli import cli


def _write_legacy_snapshot(store, agent_name="legacy agent") -> None:
    path = store / "legacy_agent.json"
    path.write_text(json.dumps({
        "agent_name": agent_name,
        "predictions": [
            {
                "id": "legacy-1",
                "claim": "legacy claim one",
                "confidence": 0.8,
                "domain": "codebase",
                "timestamp": "2026-03-24T00:00:00+00:00",
                "outcome": True,
                "verified_at": "2026-03-24T00:01:00+00:00",
                "notes": None,
            },
            {
                "id": "legacy-2",
                "claim": "legacy claim two",
                "confidence": 0.6,
                "domain": "behavior",
                "timestamp": "2026-03-25T00:00:00+00:00",
                "outcome": False,
                "verified_at": "2026-03-25T00:01:00+00:00",
                "notes": "missed",
            },
        ],
    }) + "\n")


def _record_verified_predictions(runner: CliRunner, store: str, count: int) -> None:
    """Create and verify predictions through the CLI."""
    for i in range(count):
        pid = f"cli-{i}"
        result = runner.invoke(
            cli,
            [
                "--agent",
                "cli-test",
                "--store",
                store,
                "predict",
                f"claim {i}",
                "--confidence",
                "80",
                "--domain",
                "codebase",
                "--id",
                pid,
            ],
        )
        assert result.exit_code == 0

        result = runner.invoke(
            cli,
            [
                "--agent",
                "cli-test",
                "--store",
                store,
                "verify",
                pid,
                "--correct",
            ],
        )
        assert result.exit_code == 0


def test_trajectory_command_reports_insufficient_data(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--agent",
            "cli-test",
            "--store",
            str(tmp_path),
            "trajectory",
            "--interval",
            "5",
        ],
    )

    assert result.exit_code == 0
    assert "Need at least 5 verified predictions" in result.output


def test_trajectory_command_shows_summary(tmp_path):
    runner = CliRunner()
    _record_verified_predictions(runner, str(tmp_path), count=5)

    result = runner.invoke(
        cli,
        [
            "--agent",
            "cli-test",
            "--store",
            str(tmp_path),
            "trajectory",
            "--interval",
            "5",
        ],
    )

    assert result.exit_code == 0
    assert "Trajectory: cli-test" in result.output
    assert "Snapshots: 1" in result.output


def test_cli_multi_agent_workflow_keeps_cards_separate(tmp_path):
    runner = CliRunner()
    store = str(tmp_path)

    alpha_predict = runner.invoke(
        cli,
        [
            "--agent",
            "agent alpha",
            "--store",
            store,
            "predict",
            "alpha prediction",
            "--confidence",
            "80",
            "--domain",
            "codebase",
            "--id",
            "alpha-1",
        ],
    )
    assert alpha_predict.exit_code == 0

    beta_predict = runner.invoke(
        cli,
        [
            "--agent",
            "agent/alpha",
            "--store",
            store,
            "predict",
            "beta prediction",
            "--confidence",
            "70",
            "--domain",
            "design",
            "--id",
            "beta-1",
        ],
    )
    assert beta_predict.exit_code == 0

    alpha_verify = runner.invoke(
        cli,
        ["--agent", "agent alpha", "--store", store, "verify", "alpha-1", "--correct"],
    )
    assert alpha_verify.exit_code == 0

    beta_verify = runner.invoke(
        cli,
        ["--agent", "agent/alpha", "--store", store, "verify", "beta-1", "--incorrect"],
    )
    assert beta_verify.exit_code == 0

    alpha_card = runner.invoke(
        cli,
        ["--agent", "agent alpha", "--store", store, "card", "--json"],
    )
    beta_card = runner.invoke(
        cli,
        ["--agent", "agent/alpha", "--store", store, "card", "--json"],
    )

    assert alpha_card.exit_code == 0
    assert beta_card.exit_code == 0

    alpha = json.loads(alpha_card.output)
    beta = json.loads(beta_card.output)

    assert alpha["agent_name"] == "agent alpha"
    assert alpha["calibration"]["overall_accuracy"] == 1.0
    assert alpha["calibration"]["domains"] == {
        "codebase": {
            "predictions": 1,
            "correct": 1,
            "avg_confidence": 0.8,
            "accuracy": 1.0,
        }
    }

    assert beta["agent_name"] == "agent/alpha"
    assert beta["calibration"]["overall_accuracy"] == 0.0
    assert beta["calibration"]["domains"] == {
        "design": {
            "predictions": 1,
            "correct": 0,
            "avg_confidence": 0.7,
            "accuracy": 0.0,
        }
    }

    assert (tmp_path / "agent%20alpha.json").exists()
    assert (tmp_path / "agent%2Falpha.json").exists()


def test_import_command_imports_calibrate_md(tmp_path):
    runner = CliRunner()
    source = tmp_path / "CALIBRATE.md"
    source.write_text(
        """\
# CALIBRATE.md

### [P-001] 2026-03-24 — codebase

**Prediction:** Project has fewer than 15 files.
**Confidence:** 75%
**Actual:** 10 files.
**Result:** correct
"""
    )

    result = runner.invoke(
        cli,
        [
            "--agent",
            "import-agent",
            "--store",
            str(tmp_path),
            "import",
            str(source),
        ],
    )

    assert result.exit_code == 0
    assert "Imported 1 predictions" in result.output

    card = runner.invoke(
        cli,
        ["--agent", "import-agent", "--store", str(tmp_path), "card", "--json"],
    )
    assert card.exit_code == 0
    data = json.loads(card.output)
    assert data["agent_name"] == "import-agent"
    assert data["calibration"]["total_verified"] == 1


def test_verify_log_command_reports_valid_chain(tmp_path):
    runner = CliRunner()
    _record_verified_predictions(runner, str(tmp_path), count=1)

    result = runner.invoke(
        cli,
        ["--agent", "cli-test", "--store", str(tmp_path), "verify-log"],
    )

    assert result.exit_code == 0
    assert "Event log valid: 2 event(s)" in result.output
    assert "Head: " in result.output


def test_verify_log_command_json(tmp_path):
    runner = CliRunner()
    _record_verified_predictions(runner, str(tmp_path), count=1)

    result = runner.invoke(
        cli,
        ["--agent", "cli-test", "--store", str(tmp_path), "verify-log", "--json"],
    )

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["valid"] is True
    assert data["event_count"] == 2
    assert len(data["head_hash"]) == 64


def test_verify_log_command_fails_on_wrong_expected_head(tmp_path):
    runner = CliRunner()
    _record_verified_predictions(runner, str(tmp_path), count=1)

    result = runner.invoke(
        cli,
        [
            "--agent",
            "cli-test",
            "--store",
            str(tmp_path),
            "verify-log",
            "--head",
            "0" * 64,
        ],
    )

    assert result.exit_code == 1
    assert "Event log invalid: head hash does not match expected_head" in result.output


def test_verify_log_command_fails_on_tampered_log(tmp_path):
    runner = CliRunner()
    _record_verified_predictions(runner, str(tmp_path), count=1)
    event_path = tmp_path / "cli-test.events.jsonl"
    lines = event_path.read_text().splitlines()
    event = json.loads(lines[0])
    event["payload"]["prediction"]["claim"] = "tampered"
    lines[0] = json.dumps(event, sort_keys=True, separators=(",", ":"))
    event_path.write_text("\n".join(lines) + "\n")

    result = runner.invoke(
        cli,
        ["--agent", "cli-test", "--store", str(tmp_path), "verify-log"],
    )

    assert result.exit_code == 1
    assert "Event log invalid: prev_hash does not match previous line hash" in result.output
    assert "Failed line: 2" in result.output


def test_anchor_command_appends_anchor_and_keeps_card_replay_working(tmp_path):
    runner = CliRunner()
    _record_verified_predictions(runner, str(tmp_path), count=1)

    anchor = runner.invoke(
        cli,
        [
            "--agent",
            "cli-test",
            "--store",
            str(tmp_path),
            "anchor",
            "--label",
            "release-candidate",
            "--json",
        ],
    )

    assert anchor.exit_code == 0
    data = json.loads(anchor.output)
    assert data["event_count_before"] == 2
    assert data["event_count_after"] == 3
    assert data["label"] == "release-candidate"
    assert data["anchored_head"] != data["new_head"]

    event_path = tmp_path / "cli-test.events.jsonl"
    events = [json.loads(line) for line in event_path.read_text().splitlines()]
    assert events[-1]["type"] == "anchor"
    assert events[-1]["payload"]["anchored_head"] == data["anchored_head"]

    verify = runner.invoke(
        cli,
        [
            "--agent",
            "cli-test",
            "--store",
            str(tmp_path),
            "verify-log",
            "--head",
            data["new_head"],
        ],
    )
    assert verify.exit_code == 0

    card = runner.invoke(
        cli,
        ["--agent", "cli-test", "--store", str(tmp_path), "card", "--json"],
    )
    assert card.exit_code == 0
    assert json.loads(card.output)["calibration"]["total_verified"] == 1


def test_anchor_command_fails_on_invalid_log(tmp_path):
    runner = CliRunner()
    _record_verified_predictions(runner, str(tmp_path), count=1)
    event_path = tmp_path / "cli-test.events.jsonl"
    lines = event_path.read_text().splitlines()
    event = json.loads(lines[0])
    event["payload"]["prediction"]["claim"] = "tampered"
    lines[0] = json.dumps(event, sort_keys=True, separators=(",", ":"))
    event_path.write_text("\n".join(lines) + "\n")

    result = runner.invoke(
        cli,
        ["--agent", "cli-test", "--store", str(tmp_path), "anchor"],
    )

    assert result.exit_code == 1
    assert "Error: event log invalid" in result.output


def test_migrate_command_converts_legacy_json_and_preserves_card_stats(tmp_path):
    runner = CliRunner()
    _write_legacy_snapshot(tmp_path)

    before = runner.invoke(
        cli,
        ["--agent", "legacy agent", "--store", str(tmp_path), "card", "--json"],
    )
    assert before.exit_code == 0
    before_card = json.loads(before.output)

    migrated = runner.invoke(
        cli,
        ["--agent", "legacy agent", "--store", str(tmp_path), "migrate", "--json"],
    )

    assert migrated.exit_code == 0
    migration = json.loads(migrated.output)
    assert migration["ok"] is True
    assert migration["migrated_count"] == 2
    assert len(migration["head_hash"]) == 64

    event_path = tmp_path / "legacy%20agent.events.jsonl"
    events = [json.loads(line) for line in event_path.read_text().splitlines()]
    assert [event["type"] for event in events] == ["imported", "imported"]
    assert events[0]["payload"]["origin"] == "migrated"

    verify = runner.invoke(
        cli,
        [
            "--agent",
            "legacy agent",
            "--store",
            str(tmp_path),
            "verify-log",
            "--head",
            migration["head_hash"],
        ],
    )
    assert verify.exit_code == 0

    after = runner.invoke(
        cli,
        ["--agent", "legacy agent", "--store", str(tmp_path), "card", "--json"],
    )
    assert after.exit_code == 0
    after_card = json.loads(after.output)
    assert after_card["calibration"] == before_card["calibration"]


def test_migrate_command_refuses_existing_event_log(tmp_path):
    runner = CliRunner()
    _record_verified_predictions(runner, str(tmp_path), count=1)

    result = runner.invoke(
        cli,
        ["--agent", "cli-test", "--store", str(tmp_path), "migrate"],
    )

    assert result.exit_code == 1
    assert "event log already exists" in result.output


def test_verify_card_command_accepts_matching_card(tmp_path):
    runner = CliRunner()
    _record_verified_predictions(runner, str(tmp_path), count=3)
    card = runner.invoke(
        cli,
        ["--agent", "cli-test", "--store", str(tmp_path), "card", "--json"],
    )
    assert card.exit_code == 0
    card_path = tmp_path / "card.json"
    card_path.write_text(card.output)

    result = runner.invoke(
        cli,
        [
            "--agent",
            "cli-test",
            "--store",
            str(tmp_path),
            "verify-card",
            str(card_path),
        ],
    )

    assert result.exit_code == 0
    assert "Card verified:" in result.output
    assert "Checked: calibration" in result.output


def test_verify_card_command_accepts_matching_integrity_card(tmp_path):
    runner = CliRunner()
    _record_verified_predictions(runner, str(tmp_path), count=25)
    card = runner.invoke(
        cli,
        [
            "--agent",
            "cli-test",
            "--store",
            str(tmp_path),
            "card",
            "--with-integrity",
            "--json",
        ],
    )
    assert card.exit_code == 0
    card_path = tmp_path / "card-with-integrity.json"
    card_path.write_text(card.output)

    result = runner.invoke(
        cli,
        [
            "--agent",
            "cli-test",
            "--store",
            str(tmp_path),
            "verify-card",
            str(card_path),
            "--json",
        ],
    )

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["valid"] is True
    assert data["checked"] == ["calibration", "integrity"]


def test_verify_card_command_rejects_tampered_statistic(tmp_path):
    runner = CliRunner()
    _record_verified_predictions(runner, str(tmp_path), count=3)
    card = runner.invoke(
        cli,
        ["--agent", "cli-test", "--store", str(tmp_path), "card", "--json"],
    )
    assert card.exit_code == 0
    data = json.loads(card.output)
    data["calibration"]["total_verified"] = 99
    card_path = tmp_path / "tampered-card.json"
    card_path.write_text(json.dumps(data) + "\n")

    result = runner.invoke(
        cli,
        [
            "--agent",
            "cli-test",
            "--store",
            str(tmp_path),
            "verify-card",
            str(card_path),
        ],
    )

    assert result.exit_code == 1
    assert "Card verification failed:" in result.output
    assert "$.calibration.total_verified" in result.output


def test_verify_card_command_rejects_agent_mismatch(tmp_path):
    runner = CliRunner()
    _record_verified_predictions(runner, str(tmp_path), count=1)
    card = runner.invoke(
        cli,
        ["--agent", "cli-test", "--store", str(tmp_path), "card", "--json"],
    )
    assert card.exit_code == 0
    card_path = tmp_path / "card.json"
    card_path.write_text(card.output)

    result = runner.invoke(
        cli,
        [
            "--agent",
            "other-agent",
            "--store",
            str(tmp_path),
            "verify-card",
            str(card_path),
        ],
    )

    assert result.exit_code == 1
    assert "does not match selected agent" in result.output


def test_mcp_config_prints_json(tmp_path):
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "mcp-config",
            "--cwd",
            str(tmp_path),
            "--python",
            "python3.12",
        ],
    )

    assert result.exit_code == 0
    data = json.loads(result.output)
    config = data["mcpServers"]["caliber"]
    assert config["command"] == "python3.12"
    assert config["args"] == ["-m", "caliber.mcp_server"]
    assert config["cwd"] == str(tmp_path)


def test_mcp_config_install_merges_existing_config_and_keeps_backup(tmp_path):
    runner = CliRunner()
    config_path = tmp_path / ".mcp.json"
    config_path.write_text(json.dumps({
        "mcpServers": {
            "other": {
                "command": "node",
                "args": ["server.js"],
            }
        }
    }) + "\n")

    result = runner.invoke(
        cli,
        [
            "mcp-config",
            "--install",
            "--path",
            str(config_path),
            "--cwd",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    data = json.loads(config_path.read_text())
    assert data["mcpServers"]["other"]["command"] == "node"
    assert data["mcpServers"]["caliber"] == {
        "command": "python3",
        "args": ["-m", "caliber.mcp_server"],
        "cwd": str(tmp_path),
    }
    assert list(tmp_path.glob(".mcp.json.*.bak"))


def test_integrity_command_insufficient_data(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--agent", "cli-test", "--store", str(tmp_path), "integrity"],
    )
    assert result.exit_code == 0
    assert "nothing to analyze" in result.output


def test_integrity_command_flags_farming(tmp_path):
    runner = CliRunner()
    _record_verified_predictions(runner, str(tmp_path), 25)

    result = runner.invoke(
        cli,
        ["--agent", "cli-test", "--store", str(tmp_path), "integrity"],
    )
    assert result.exit_code == 0
    assert "Integrity Report: cli-test" in result.output
    # All-correct single-domain instant-verified record must be flagged
    assert "LOW_OUTCOME_VARIANCE" in result.output
    assert "DOMAIN_CONCENTRATION" in result.output
    assert "INSTANT_VERIFICATION" in result.output


def test_integrity_command_json(tmp_path):
    runner = CliRunner()
    _record_verified_predictions(runner, str(tmp_path), 25)

    result = runner.invoke(
        cli,
        ["--agent", "cli-test", "--store", str(tmp_path), "integrity", "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["agent_name"] == "cli-test"
    assert data["n_verified"] == 25
    codes = [f["code"] for f in data["flags"]]
    assert "LOW_OUTCOME_VARIANCE" in codes
    assert "metrics" in data


def test_card_with_integrity(tmp_path):
    runner = CliRunner()
    _record_verified_predictions(runner, str(tmp_path), 25)

    result = runner.invoke(
        cli,
        ["--agent", "cli-test", "--store", str(tmp_path),
         "card", "--with-integrity", "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "calibration" in data
    assert "integrity" in data
    assert data["integrity"]["n_verified"] == 25
    assert data["integrity"]["flags"]

    text = runner.invoke(
        cli,
        ["--agent", "cli-test", "--store", str(tmp_path),
         "card", "--with-integrity"],
    )
    assert text.exit_code == 0
    assert "Trust Card: cli-test" in text.output
    assert "Integrity Report: cli-test" in text.output


def test_card_without_integrity_unchanged(tmp_path):
    runner = CliRunner()
    _record_verified_predictions(runner, str(tmp_path), 25)

    result = runner.invoke(
        cli,
        ["--agent", "cli-test", "--store", str(tmp_path), "card", "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "integrity" not in data
