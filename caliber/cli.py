"""CLI for caliber — Trust protocol for AI agents.

Usage:
    caliber predict "claim" --confidence 80 --domain codebase
    caliber verify P-001 --correct
    caliber card [--json]
    caliber summary
    caliber list [--unverified]
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

from caliber.tracker import TrustTracker
from caliber.storage import FileStorage

DEFAULT_STORE = Path.home() / ".caliber"


def _get_tracker(agent: str, store: str) -> TrustTracker:
    return TrustTracker(agent, storage=FileStorage(store))


def _mcp_server_config(python_cmd: str, cwd: str) -> dict:
    return {
        "command": python_cmd,
        "args": ["-m", "caliber.mcp_server"],
        "cwd": cwd,
    }


@click.group()
@click.option("--agent", "-a", default="default", help="Agent name.")
@click.option("--store", "-s", default=str(DEFAULT_STORE), help="Storage directory.")
@click.pass_context
def cli(ctx, agent: str, store: str):
    """caliber — Trust protocol for AI agents."""
    ctx.ensure_object(dict)
    ctx.obj["agent"] = agent
    ctx.obj["store"] = store


@cli.command()
@click.argument("claim")
@click.option("--confidence", "-c", required=True, type=float,
              help="Confidence level (50-99, or 0.50-0.99).")
@click.option("--domain", "-d", required=True, help="Prediction domain.")
@click.option("--id", "prediction_id", default=None, help="Explicit prediction ID.")
@click.pass_context
def predict(ctx, claim: str, confidence: float, domain: str, prediction_id: str):
    """Record a prediction before verifying it."""
    # Accept both 80 and 0.80
    if confidence >= 1.0:
        confidence = confidence / 100

    tracker = _get_tracker(ctx.obj["agent"], ctx.obj["store"])
    pid = tracker.predict(claim, confidence=confidence, domain=domain,
                          prediction_id=prediction_id)
    click.echo(f"Recorded: {pid}")
    click.echo(f"  Claim: {claim}")
    click.echo(f"  Confidence: {confidence:.0%}")
    click.echo(f"  Domain: {domain}")


@cli.command()
@click.argument("prediction_id")
@click.option("--correct/--incorrect", required=True, help="Was the prediction correct?")
@click.option("--notes", "-n", default=None, help="What this reveals.")
@click.pass_context
def verify(ctx, prediction_id: str, correct: bool, notes: str):
    """Record the outcome of a prediction."""
    tracker = _get_tracker(ctx.obj["agent"], ctx.obj["store"])
    try:
        pred = tracker.verify(prediction_id, correct=correct, notes=notes)
    except KeyError:
        click.echo(f"Error: No prediction with id '{prediction_id}'", err=True)
        sys.exit(1)
    result = "correct" if correct else "incorrect"
    click.echo(f"Verified {prediction_id}: {result}")
    if notes:
        click.echo(f"  Notes: {notes}")


@cli.command()
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def card(ctx, as_json: bool):
    """Generate a Trust Card from accumulated predictions."""
    tracker = _get_tracker(ctx.obj["agent"], ctx.obj["store"])
    if not tracker.verified:
        click.echo("No verified predictions yet. Use 'caliber predict' and 'caliber verify' first.")
        sys.exit(1)

    trust_card = tracker.generate_card()
    if as_json:
        click.echo(trust_card.to_json())
    else:
        click.echo(trust_card.summary())


@cli.command()
@click.pass_context
def summary(ctx):
    """Quick stats without generating a full Trust Card."""
    tracker = _get_tracker(ctx.obj["agent"], ctx.obj["store"])
    total = len(tracker.predictions)
    verified = len(tracker.verified)
    unverified = len(tracker.unverified)

    click.echo(f"Agent: {ctx.obj['agent']}")
    click.echo(f"Total predictions: {total}")
    click.echo(f"  Verified: {verified}")
    click.echo(f"  Unverified: {unverified}")

    if verified:
        correct = sum(1 for p in tracker.verified if p.outcome)
        avg_conf = sum(p.confidence for p in tracker.verified) / verified
        click.echo(f"  Accuracy: {correct/verified:.1%} ({correct}/{verified})")
        click.echo(f"  Avg confidence: {avg_conf:.1%}")
        gap = avg_conf - correct/verified
        if abs(gap) < 0.05:
            click.echo(f"  Calibration: well-calibrated")
        elif gap > 0:
            click.echo(f"  Calibration: overconfident by {gap:.0%}")
        else:
            click.echo(f"  Calibration: underconfident by {abs(gap):.0%}")

        # Early insights
        if verified >= 5:
            # Domain breakdown
            domains = {}
            for p in tracker.verified:
                domains.setdefault(p.domain, [0, 0])
                domains[p.domain][0] += 1
                if p.outcome:
                    domains[p.domain][1] += 1
            if len(domains) > 1:
                weakest = min(domains.items(), key=lambda x: x[1][1]/x[1][0] if x[1][0] else 1)
                strongest = max(domains.items(), key=lambda x: x[1][1]/x[1][0] if x[1][0] else 0)
                if weakest[0] != strongest[0]:
                    click.echo(f"  Strongest: {strongest[0]} ({strongest[1][1]}/{strongest[1][0]})")
                    click.echo(f"  Weakest: {weakest[0]} ({weakest[1][1]}/{weakest[1][0]})")

        if verified < 20:
            click.echo(f"\n  Need {20 - verified} more predictions for meaningful Trust Card.")
        elif verified < 100:
            click.echo(f"\n  Need ~{100 - verified} more per bucket for statistical significance.")


@cli.command()
@click.pass_context
def badge(ctx):
    """Generate a shields.io badge URL for your Trust Card."""
    tracker = _get_tracker(ctx.obj["agent"], ctx.obj["store"])
    if not tracker.verified:
        click.echo("No verified predictions yet.")
        sys.exit(1)

    correct = sum(1 for p in tracker.verified if p.outcome)
    total = len(tracker.verified)
    accuracy = correct / total
    avg_conf = sum(p.confidence for p in tracker.verified) / total
    gap = abs(avg_conf - accuracy)

    if gap < 0.05:
        label = "well calibrated"
        color = "brightgreen"
    elif gap < 0.10:
        label = "slightly miscalibrated"
        color = "yellow"
    else:
        label = "miscalibrated"
        color = "orange"

    agent = ctx.obj["agent"]
    badge_url = (
        f"https://img.shields.io/badge/"
        f"caliber-{accuracy:.0%}%20({total}%20preds%2C%20{label})-{color}"
    )
    markdown = f"![{agent} Trust Card]({badge_url})"
    click.echo(f"Badge URL: {badge_url}")
    click.echo(f"Markdown:  {markdown}")


@cli.command("list")
@click.option("--unverified", is_flag=True, help="Show only unverified predictions.")
@click.option("--domain", "-d", default=None, help="Filter by domain.")
@click.pass_context
def list_predictions(ctx, unverified: bool, domain: str):
    """List predictions."""
    tracker = _get_tracker(ctx.obj["agent"], ctx.obj["store"])
    preds = tracker.unverified if unverified else tracker.predictions

    if domain:
        preds = [p for p in preds if p.domain == domain]

    if not preds:
        click.echo("No predictions found.")
        return

    for p in preds:
        status = ""
        if p.outcome is True:
            status = " [correct]"
        elif p.outcome is False:
            status = " [incorrect]"
        else:
            status = " [pending]"

        click.echo(f"{p.id} ({p.confidence:.0%}, {p.domain}){status}")
        click.echo(f"  {p.claim}")


@cli.command("import")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--format", "fmt", type=click.Choice(["auto", "md", "csv"]),
              default="auto", help="Import format.")
@click.pass_context
def import_data(ctx, file_path: str, fmt: str):
    """Import predictions from a file.

    Supported formats: CALIBRATE.md (markdown), CSV.
    Auto-detect by file extension.
    """
    from caliber.importer import import_calibrate_md, import_csv

    tracker = _get_tracker(ctx.obj["agent"], ctx.obj["store"])

    if fmt == "auto":
        if file_path.endswith(".csv"):
            fmt = "csv"
        else:
            fmt = "md"

    if fmt == "md":
        count = import_calibrate_md(file_path, tracker)
    else:
        count = import_csv(file_path, tracker)

    click.echo(f"Imported {count} predictions from {file_path}")


@cli.command()
@click.option("--interval", "-i", default=10, help="Predictions per snapshot.")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def trajectory(ctx, interval: int, as_json: bool):
    """Show how calibration changes over time."""
    from caliber.trajectory import Trajectory

    tracker = _get_tracker(ctx.obj["agent"], ctx.obj["store"])
    if len(tracker.verified) < interval:
        click.echo(f"Need at least {interval} verified predictions for trajectory.")
        return

    traj = Trajectory.from_predictions(ctx.obj["agent"], tracker.verified, interval=interval)
    if as_json:
        import json
        click.echo(json.dumps(traj.to_dict(), indent=2))
    else:
        click.echo(traj.summary())


@cli.command("mcp-config")
@click.option("--install", is_flag=True, help="Write the config into an MCP JSON file.")
@click.option(
    "--path",
    "config_path",
    default=str(Path.home() / ".mcp.json"),
    help="MCP JSON config path used with --install.",
)
@click.option("--server-name", default="caliber", help="MCP server name.")
@click.option("--python", "python_cmd", default="python3", help="Python command.")
@click.option(
    "--cwd",
    default=None,
    help="Working directory for the MCP server. Defaults to the current directory.",
)
def mcp_config(
    install: bool,
    config_path: str,
    server_name: str,
    python_cmd: str,
    cwd: str | None,
):
    """Print or install the caliber MCP server config."""
    server_cwd = Path(cwd).expanduser().resolve() if cwd else Path.cwd().resolve()
    server_config = _mcp_server_config(python_cmd, str(server_cwd))
    snippet = {"mcpServers": {server_name: server_config}}

    if not install:
        click.echo(json.dumps(snippet, indent=2))
        return

    path = Path(config_path).expanduser()
    if path.exists():
        existing = json.loads(path.read_text())
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_path = path.with_name(f"{path.name}.{timestamp}.bak")
        backup_path.write_text(path.read_text())
    else:
        existing = {}
        backup_path = None

    if not isinstance(existing, dict):
        raise click.ClickException(f"{path} must contain a JSON object")

    servers = existing.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise click.ClickException(f"{path} field 'mcpServers' must be an object")

    servers[server_name] = server_config
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(existing, indent=2) + "\n")

    click.echo(f"Installed MCP server '{server_name}' in {path}")
    if backup_path is not None:
        click.echo(f"Backup saved: {backup_path}")


def main():
    cli()


if __name__ == "__main__":
    main()
