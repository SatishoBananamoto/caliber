"""CLI for caliber — Trust protocol for AI agents.

Usage:
    caliber predict "claim" --confidence 80 --domain codebase
    caliber verify P-001 --correct
    caliber card [--json]
    caliber summary
    caliber list [--unverified]
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from caliber.tracker import TrustTracker
from caliber.storage import FileStorage

DEFAULT_STORE = Path.home() / ".caliber"


def _get_tracker(agent: str, store: str) -> TrustTracker:
    return TrustTracker(agent, storage=FileStorage(store))


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
        click.echo(f"  Accuracy: {correct/verified:.1%} ({correct}/{verified})")


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


def main():
    cli()


if __name__ == "__main__":
    main()
