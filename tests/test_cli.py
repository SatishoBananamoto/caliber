"""Tests for caliber CLI commands."""

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
