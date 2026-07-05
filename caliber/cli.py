"""CLI for caliber — calibration instrument for AI agents.

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


def _strip_generated_fields(value):
    if isinstance(value, dict):
        return {
            key: _strip_generated_fields(item)
            for key, item in value.items()
            if key != "generated"
        }
    if isinstance(value, list):
        return [_strip_generated_fields(item) for item in value]
    return value


def _first_mismatch(expected, actual, path: str = "$") -> str | None:
    if isinstance(expected, dict) and isinstance(actual, dict):
        expected_keys = set(expected)
        actual_keys = set(actual)
        missing = sorted(expected_keys - actual_keys)
        if missing:
            return f"{path}.{missing[0]} missing from saved card"
        unexpected = sorted(actual_keys - expected_keys)
        if unexpected:
            return f"{path}.{unexpected[0]} unexpected in saved card"
        for key in sorted(expected):
            mismatch = _first_mismatch(expected[key], actual[key], f"{path}.{key}")
            if mismatch:
                return mismatch
        return None

    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return f"{path} length expected {len(expected)}, got {len(actual)}"
        for index, (expected_item, actual_item) in enumerate(zip(expected, actual)):
            mismatch = _first_mismatch(
                expected_item,
                actual_item,
                f"{path}[{index}]",
            )
            if mismatch:
                return mismatch
        return None

    if expected != actual:
        return f"{path} expected {expected!r}, got {actual!r}"
    return None


@click.group()
@click.option("--agent", "-a", default="default", help="Agent name.")
@click.option("--store", "-s", default=str(DEFAULT_STORE), help="Storage directory.")
@click.pass_context
def cli(ctx, agent: str, store: str):
    """caliber — calibration instrument for AI agents."""
    ctx.ensure_object(dict)
    ctx.obj["agent"] = agent
    ctx.obj["store"] = store


@cli.command("keygen")
@click.option("--force", is_flag=True, help="Replace an existing signing keypair.")
@click.pass_context
def keygen(ctx, force: bool):
    """Generate an optional Ed25519 signing keypair for Trust Cards."""
    from caliber.signing import SigningUnavailable, generate_keypair

    try:
        paths = generate_keypair(
            ctx.obj["store"],
            ctx.obj["agent"],
            force=force,
        )
    except SigningUnavailable as exc:
        raise click.ClickException(str(exc)) from exc
    except FileExistsError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Private key: {paths.private_key}")
    click.echo(f"Public key:  {paths.public_key}")
    click.echo("Private key permissions set to 0600.")


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
@click.argument("prediction_id")
@click.option("--correct/--incorrect", required=True, help="Was the prediction correct?")
@click.option("--by", "adjudicator", required=True, help="Adjudicator identity.")
@click.option("--evidence-note", default=None, help="Optional evidence note.")
@click.option("--signature", "adjudicator_signature", default=None,
              help="Optional adjudicator signature.")
@click.pass_context
def adjudicate(
    ctx,
    prediction_id: str,
    correct: bool,
    adjudicator: str,
    evidence_note: str | None,
    adjudicator_signature: str | None,
):
    """Record an externally adjudicated outcome for a prediction."""
    tracker = _get_tracker(ctx.obj["agent"], ctx.obj["store"])
    try:
        tracker.adjudicate(
            prediction_id,
            correct=correct,
            adjudicator=adjudicator,
            evidence_note=evidence_note,
            adjudicator_signature=adjudicator_signature,
        )
    except KeyError:
        click.echo(f"Error: No prediction with id '{prediction_id}'", err=True)
        sys.exit(1)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    result = "correct" if correct else "incorrect"
    click.echo(f"Adjudicated {prediction_id}: {result}")
    click.echo(f"  By: {adjudicator}")
    if evidence_note:
        click.echo(f"  Evidence: {evidence_note}")


@cli.command()
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@click.option("--with-integrity", "with_integrity", is_flag=True,
              help="Attach the gaming-signature analysis to the card.")
@click.option("--sign", is_flag=True, help="Sign the card with the store keypair.")
@click.option(
    "--key",
    "private_key",
    type=click.Path(exists=True),
    default=None,
    help="Private key path for --sign. Defaults to the store keypair.",
)
@click.pass_context
def card(ctx, as_json: bool, with_integrity: bool, sign: bool, private_key: str | None):
    """Generate a Trust Card from accumulated predictions."""
    tracker = _get_tracker(ctx.obj["agent"], ctx.obj["store"])
    if not tracker.verified:
        click.echo("No verified predictions yet. Use 'caliber predict' and 'caliber verify' first.")
        sys.exit(1)

    trust_card = tracker.generate_card()
    report = None
    if with_integrity:
        from caliber.integrity import IntegrityReport
        report = IntegrityReport.from_predictions(
            ctx.obj["agent"], tracker.predictions
        )

    card_dict = trust_card.to_dict()
    if report is not None:
        card_dict["integrity"] = report.to_dict()

    if sign:
        from caliber.event_log import EventLog
        from caliber.signing import (
            SigningUnavailable,
            default_key_paths,
            sign_card,
        )

        log = EventLog(ctx.obj["store"])
        event_path = log.path_for(ctx.obj["agent"])
        if not event_path.exists():
            raise click.ClickException(
                f"cannot sign card: no event log found for {ctx.obj['agent']!r}"
            )
        verification = log.verify(ctx.obj["agent"])
        if not verification.valid:
            raise click.ClickException(
                f"cannot sign card: event log invalid: {verification.error}"
            )
        key_path = Path(private_key) if private_key else default_key_paths(
            ctx.obj["store"],
            ctx.obj["agent"],
        ).private_key
        try:
            card_dict = sign_card(card_dict, verification.head_hash, key_path)
        except SigningUnavailable as exc:
            raise click.ClickException(str(exc)) from exc
        except (OSError, ValueError) as exc:
            raise click.ClickException(f"cannot sign card: {exc}") from exc

    if as_json or sign:
        click.echo(json.dumps(card_dict, indent=2))
    else:
        click.echo(trust_card.summary())
        if report is not None:
            click.echo()
            click.echo(report.summary())


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


@cli.command()
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def integrity(ctx, as_json: bool):
    """Check the prediction record for gaming signatures.

    Runs deterministic statistics (Brier decomposition, concentration,
    duplicate claims, verification latency) and reports advisory flags
    with evidence. Calibration can be farmed; these signals cannot.
    """
    from caliber.integrity import IntegrityReport

    tracker = _get_tracker(ctx.obj["agent"], ctx.obj["store"])
    report = IntegrityReport.from_predictions(
        ctx.obj["agent"], tracker.predictions
    )
    if as_json:
        click.echo(json.dumps(report.to_dict(), indent=2))
    else:
        click.echo(report.summary())


@cli.command("verify-log")
@click.option("--head", "expected_head", default=None,
              help="Expected chain head hash from an external anchor.")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def verify_log(ctx, expected_head: str | None, as_json: bool):
    """Verify the append-only event-log hash chain."""
    from caliber.event_log import EventLog

    log = EventLog(ctx.obj["store"])
    path = log.path_for(ctx.obj["agent"])
    if not path.exists():
        result = {
            "agent_name": ctx.obj["agent"],
            "path": str(path),
            "valid": False,
            "event_count": 0,
            "head_hash": None,
            "error": "No event log found.",
            "failed_line": None,
        }
        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Error: {result['error']} ({path})", err=True)
        sys.exit(1)

    verification = log.verify(ctx.obj["agent"], expected_head=expected_head)
    result = {
        "agent_name": ctx.obj["agent"],
        "path": str(path),
        "valid": verification.valid,
        "event_count": verification.event_count,
        "head_hash": verification.head_hash,
        "error": verification.error,
        "failed_line": verification.failed_line,
    }
    if as_json:
        click.echo(json.dumps(result, indent=2))
    elif verification.valid:
        click.echo(f"Event log valid: {verification.event_count} event(s)")
        click.echo(f"Head: {verification.head_hash}")
        click.echo(f"Path: {path}")
    else:
        click.echo(f"Event log invalid: {verification.error}", err=True)
        if verification.failed_line is not None:
            click.echo(f"Failed line: {verification.failed_line}", err=True)
        click.echo(f"Head: {verification.head_hash}", err=True)

    if not verification.valid:
        sys.exit(1)


@cli.command("anchor")
@click.option("--label", default=None, help="Optional local label for this anchor.")
@click.option(
    "--emit",
    "emit_path",
    type=click.Path(),
    default=None,
    help="Append the anchor result to a separate JSONL anchors file.",
)
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def anchor(ctx, label: str | None, emit_path: str | None, as_json: bool):
    """Append and print an anchor event for the current event-log head."""
    from caliber.event_log import EventLog

    log = EventLog(ctx.obj["store"])
    path = log.path_for(ctx.obj["agent"])
    if not path.exists():
        result = {
            "agent_name": ctx.obj["agent"],
            "path": str(path),
            "anchored_head": None,
            "new_head": None,
            "event_count_before": 0,
            "event_count_after": 0,
            "label": label,
            "emit_path": emit_path,
            "error": "No event log found.",
        }
        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Error: {result['error']} ({path})", err=True)
        sys.exit(1)

    verification = log.verify(ctx.obj["agent"])
    if not verification.valid:
        result = {
            "agent_name": ctx.obj["agent"],
            "path": str(path),
            "anchored_head": None,
            "new_head": verification.head_hash,
            "event_count_before": verification.event_count,
            "event_count_after": verification.event_count,
            "label": label,
            "emit_path": emit_path,
            "error": verification.error,
        }
        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Error: event log invalid: {verification.error}", err=True)
        sys.exit(1)

    payload = {
        "anchored_head": verification.head_hash,
        "anchored_event_count": verification.event_count,
        "label": label,
    }
    appended = log.append(ctx.obj["agent"], "anchor", payload)
    result = {
        "agent_name": ctx.obj["agent"],
        "path": str(path),
        "anchored_head": verification.head_hash,
        "new_head": appended.line_hash,
        "event_count_before": verification.event_count,
        "event_count_after": verification.event_count + 1,
        "label": label,
        "emit_path": emit_path,
        "error": None,
    }
    if emit_path is not None:
        anchor_record = {
            "version": 1,
            "agent_name": ctx.obj["agent"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "anchored_head": verification.head_hash,
            "new_head": appended.line_hash,
            "event_count_before": verification.event_count,
            "event_count_after": verification.event_count + 1,
            "label": label,
        }
        anchor_path = Path(emit_path).expanduser()
        anchor_path.parent.mkdir(parents=True, exist_ok=True)
        with anchor_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(anchor_record, sort_keys=True) + "\n")

    if as_json:
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Anchored head: {verification.head_hash}")
        click.echo(f"New head:      {appended.line_hash}")
        click.echo(f"Events:        {verification.event_count} -> {verification.event_count + 1}")
        click.echo(f"Path:          {path}")
        if label:
            click.echo(f"Label:         {label}")
        if emit_path:
            click.echo(f"Emitted to:    {Path(emit_path).expanduser()}")
        click.echo("Use the new head with: caliber verify-log --head <new-head>")


@cli.command("migrate")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
def migrate(ctx, as_json: bool):
    """Migrate a legacy JSON snapshot into an event log."""
    storage = FileStorage(ctx.obj["store"])
    try:
        result = storage.migrate_snapshot(ctx.obj["agent"])
    except (FileNotFoundError, ValueError) as exc:
        if as_json:
            click.echo(json.dumps({
                "agent_name": ctx.obj["agent"],
                "ok": False,
                "error": str(exc),
            }, indent=2))
        else:
            click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    result = {"ok": True, **result}
    if as_json:
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Migrated {result['migrated_count']} prediction(s)")
        click.echo(f"Event log: {result['event_log_path']}")
        click.echo(f"Head:      {result['head_hash']}")
        click.echo("Migration marks existing records as imported/unwitnessed history.")


@cli.command("verify-card")
@click.argument("card_path", type=click.Path(exists=True))
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@click.option(
    "--pubkey",
    type=click.Path(exists=True),
    default=None,
    help="Verify a signed card with this Ed25519 public key.",
)
@click.pass_context
def verify_card(ctx, card_path: str, as_json: bool, pubkey: str | None):
    """Verify a saved Trust Card against the event-log-backed store."""
    from caliber.event_log import EventLog
    from caliber.signing import (
        SIGNATURE_FIELD,
        SignatureVerificationError,
        SigningUnavailable,
        strip_signature,
        verify_card_signature,
    )

    path = Path(card_path)
    try:
        saved_card = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"{path} is not valid JSON: {exc}") from exc

    agent_name = ctx.obj["agent"]
    card_agent = saved_card.get("agent_name")
    if card_agent != agent_name:
        result = {
            "card_path": str(path),
            "agent_name": agent_name,
            "valid": False,
            "error": (
                f"card agent_name {card_agent!r} does not match selected "
                f"agent {agent_name!r}"
            ),
        }
        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Error: {result['error']}", err=True)
        sys.exit(1)

    log = EventLog(ctx.obj["store"])
    event_path = log.path_for(agent_name)
    if not event_path.exists():
        result = {
            "card_path": str(path),
            "agent_name": agent_name,
            "valid": False,
            "error": f"No event log found for {agent_name!r}.",
        }
        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Error: {result['error']}", err=True)
        sys.exit(1)

    log_verification = log.verify(agent_name)
    if not log_verification.valid:
        result = {
            "card_path": str(path),
            "agent_name": agent_name,
            "valid": False,
            "error": f"event log invalid: {log_verification.error}",
        }
        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Error: {result['error']}", err=True)
        sys.exit(1)

    checked = ["calibration"]
    if pubkey is not None:
        try:
            verify_card_signature(
                saved_card,
                pubkey,
                current_event_log_head=log_verification.head_hash,
            )
        except SigningUnavailable as exc:
            result = {
                "card_path": str(path),
                "agent_name": agent_name,
                "valid": False,
                "checked": checked,
                "event_log_head": log_verification.head_hash,
                "event_count": log_verification.event_count,
                "error": str(exc),
            }
            if as_json:
                click.echo(json.dumps(result, indent=2))
            else:
                click.echo(f"Card signature failed: {result['error']}", err=True)
            sys.exit(1)
        except SignatureVerificationError as exc:
            result = {
                "card_path": str(path),
                "agent_name": agent_name,
                "valid": False,
                "checked": checked,
                "event_log_head": log_verification.head_hash,
                "event_count": log_verification.event_count,
                "error": str(exc),
            }
            if as_json:
                click.echo(json.dumps(result, indent=2))
            else:
                click.echo(f"Card signature failed: {result['error']}", err=True)
            sys.exit(1)
        checked.append("signature")

    tracker = _get_tracker(agent_name, ctx.obj["store"])
    recomputed = tracker.generate_card().to_dict()
    if "integrity" in saved_card:
        from caliber.integrity import IntegrityReport

        report = IntegrityReport.from_predictions(agent_name, tracker.predictions)
        recomputed["integrity"] = report.to_dict()
        checked.append("integrity")

    expected = _strip_generated_fields(recomputed)
    actual_card = (
        strip_signature(saved_card)
        if SIGNATURE_FIELD in saved_card
        else saved_card
    )
    actual = _strip_generated_fields(actual_card)
    mismatch = _first_mismatch(expected, actual)
    result = {
        "card_path": str(path),
        "agent_name": agent_name,
        "valid": mismatch is None,
        "checked": checked,
        "event_log_head": log_verification.head_hash,
        "event_count": log_verification.event_count,
        "error": mismatch,
    }
    if as_json:
        click.echo(json.dumps(result, indent=2))
    elif mismatch is None:
        click.echo(f"Card verified: {path}")
        click.echo(f"Checked: {', '.join(checked)}")
        click.echo(f"Event log head: {log_verification.head_hash}")
    else:
        click.echo(f"Card verification failed: {mismatch}", err=True)

    if mismatch is not None:
        sys.exit(1)


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
