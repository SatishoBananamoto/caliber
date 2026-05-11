"""Tests for caliber CLI commands."""

import json

from click.testing import CliRunner

from caliber.cli import cli


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
