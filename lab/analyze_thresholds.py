"""Analyze threshold operating points from simulated integrity metrics."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from caliber.integrity import (  # noqa: E402
    DOMAIN_HHI_THRESHOLD,
    DUPLICATE_RATIO_THRESHOLD,
    IMPORT_SHARE_THRESHOLD,
    INSTANT_SHARE_THRESHOLD,
    LOW_RESOLUTION_RATIO,
    LOW_UNCERTAINTY_THRESHOLD,
    MENDEL_P_LOW_THRESHOLD,
    TOP_BUCKET_SHARE_THRESHOLD,
    IntegrityReport,
)
from lab import simulate  # noqa: E402


DEFAULT_REPLICATES = 500
DEFAULT_N = 50
DEFAULT_BASE_SEED = 9301
RESULTS_DIR = Path(__file__).parent / "results"
REPORT_PATH = Path(__file__).parent / "THRESHOLDS.md"

CLEAN_POPULATIONS = (
    "honest",
    "overconfident",
    "underconfident",
    "noisy",
    "smart_fabricator",
)


@dataclass(frozen=True)
class ThresholdSpec:
    constant: str
    metric: str
    direction: str
    current: float
    targets: tuple[str, ...]
    flag_code: str


SPECS = (
    ThresholdSpec(
        "LOW_UNCERTAINTY_THRESHOLD",
        "uncertainty",
        "low",
        LOW_UNCERTAINTY_THRESHOLD,
        ("farmer", "patient_farmer"),
        "LOW_OUTCOME_VARIANCE",
    ),
    ThresholdSpec(
        "LOW_RESOLUTION_RATIO",
        "resolution_ratio",
        "low",
        LOW_RESOLUTION_RATIO,
        ("naive_fabricator", "template_spammer"),
        "NO_DISCRIMINATION",
    ),
    ThresholdSpec(
        "TOP_BUCKET_SHARE_THRESHOLD",
        "top_bucket_share",
        "high",
        TOP_BUCKET_SHARE_THRESHOLD,
        ("farmer", "patient_farmer"),
        "CONFIDENCE_CONCENTRATION",
    ),
    ThresholdSpec(
        "DOMAIN_HHI_THRESHOLD",
        "domain_hhi",
        "high",
        DOMAIN_HHI_THRESHOLD,
        ("domain_camper",),
        "DOMAIN_CONCENTRATION",
    ),
    ThresholdSpec(
        "DUPLICATE_RATIO_THRESHOLD",
        "duplicate_claim_ratio",
        "high",
        DUPLICATE_RATIO_THRESHOLD,
        ("duplicate_spammer",),
        "DUPLICATE_CLAIMS",
    ),
    ThresholdSpec(
        "INSTANT_SHARE_THRESHOLD",
        "instant_verify_share",
        "high",
        INSTANT_SHARE_THRESHOLD,
        ("farmer",),
        "INSTANT_VERIFICATION",
    ),
    ThresholdSpec(
        "IMPORT_SHARE_THRESHOLD",
        "import_share",
        "high",
        IMPORT_SHARE_THRESHOLD,
        ("bulk_importer",),
        "UNWITNESSED_HISTORY",
    ),
    ThresholdSpec(
        "MENDEL_P_LOW_THRESHOLD",
        "mendel_p_low",
        "low",
        MENDEL_P_LOW_THRESHOLD,
        ("naive_fabricator",),
        "SUSPICIOUSLY_PERFECT",
    ),
)


def git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _seed(base_seed: int, population_index: int, replicate: int) -> int:
    return base_seed + population_index * 1_000_000 + replicate


def _metric_value(report: IntegrityReport, metric: str) -> float | None:
    if metric == "resolution_ratio":
        if report.resolution is None or report.uncertainty in (None, 0):
            return None
        return report.resolution / report.uncertainty
    return getattr(report, metric)


def collect_metrics(
    *,
    n: int = DEFAULT_N,
    replicates: int = DEFAULT_REPLICATES,
    base_seed: int = DEFAULT_BASE_SEED,
) -> dict[str, list[dict[str, Any]]]:
    needed = tuple(dict.fromkeys((*CLEAN_POPULATIONS, *[p for spec in SPECS for p in spec.targets])))
    collected: dict[str, list[dict[str, Any]]] = {}
    for population_index, name in enumerate(needed):
        simulator = simulate.POPULATIONS[name]
        rows = []
        for replicate in range(replicates):
            records = simulator(n, _seed(base_seed, population_index, replicate))
            report = IntegrityReport.from_predictions(
                name,
                simulate.to_predictions(records),
            )
            rows.append(
                {
                    "flags": [flag.code for flag in report.flags],
                    "metrics": {
                        spec.metric: _metric_value(report, spec.metric)
                        for spec in SPECS
                    },
                }
            )
        collected[name] = rows
    return collected


def _fires(value: float | None, threshold: float, direction: str) -> bool:
    if value is None:
        return False
    if direction == "high":
        return value > threshold
    if direction == "low":
        return value < threshold
    raise ValueError(f"unknown direction: {direction}")


def _candidate_thresholds(spec: ThresholdSpec, metrics: dict[str, list[dict[str, Any]]]) -> list[float]:
    values = {spec.current}
    for rows in metrics.values():
        for row in rows:
            value = row["metrics"].get(spec.metric)
            if value is not None:
                values.add(float(value))
    extras = {i / 100 for i in range(0, 101)}
    values.update(extras)
    return sorted(v for v in values if 0.0 <= v <= 1.0)


def _rate(rows: list[dict[str, Any]], spec: ThresholdSpec, threshold: float) -> float:
    return sum(
        1
        for row in rows
        if _fires(row["metrics"].get(spec.metric), threshold, spec.direction)
    ) / len(rows)


def _actual_flag_rate(rows: list[dict[str, Any]], flag_code: str) -> float:
    return sum(1 for row in rows if flag_code in row["flags"]) / len(rows)


def analyze_thresholds(
    *,
    n: int = DEFAULT_N,
    replicates: int = DEFAULT_REPLICATES,
    base_seed: int = DEFAULT_BASE_SEED,
    sha: str | None = None,
) -> dict[str, Any]:
    metrics = collect_metrics(n=n, replicates=replicates, base_seed=base_seed)
    analyses = []
    clean_rows = [row for name in CLEAN_POPULATIONS for row in metrics[name]]
    for spec in SPECS:
        candidates = _candidate_thresholds(spec, metrics)
        best = None
        for threshold in candidates:
            clean_fpr = _rate(clean_rows, spec, threshold)
            if clean_fpr > 0.05:
                continue
            target_rates = {
                name: _rate(metrics[name], spec, threshold)
                for name in spec.targets
            }
            mean_power = sum(target_rates.values()) / len(target_rates)
            candidate = {
                "threshold": round(threshold, 6),
                "clean_fpr": round(clean_fpr, 4),
                "target_power_mean": round(mean_power, 4),
                "target_rates": {
                    name: round(rate, 4) for name, rate in target_rates.items()
                },
            }
            if best is None:
                best = candidate
                continue
            if candidate["target_power_mean"] > best["target_power_mean"]:
                best = candidate
            elif candidate["target_power_mean"] == best["target_power_mean"]:
                current_distance = abs(candidate["threshold"] - spec.current)
                best_distance = abs(best["threshold"] - spec.current)
                if current_distance < best_distance:
                    best = candidate

        current_clean_fpr = _rate(clean_rows, spec, spec.current)
        current_target_rates = {
            name: _rate(metrics[name], spec, spec.current)
            for name in spec.targets
        }
        analyses.append(
            {
                "constant": spec.constant,
                "metric": spec.metric,
                "direction": spec.direction,
                "flag_code": spec.flag_code,
                "current_threshold": spec.current,
                "current_clean_fpr": round(current_clean_fpr, 4),
                "current_target_rates": {
                    name: round(rate, 4)
                    for name, rate in current_target_rates.items()
                },
                "actual_current_flag_rates": {
                    name: round(_actual_flag_rate(metrics[name], spec.flag_code), 4)
                    for name in (*CLEAN_POPULATIONS, *spec.targets)
                    if name in metrics
                },
                "recommended": best,
            }
        )

    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": sha or git_sha(),
        "n": n,
        "replicates": replicates,
        "base_seed": base_seed,
        "clean_populations": list(CLEAN_POPULATIONS),
        "analyses": analyses,
    }


def write_json(result: dict[str, Any], results_dir: Path = RESULTS_DIR) -> Path:
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / f"thresholds-{result['git_sha']}.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    return path


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Caliber Threshold Analysis",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        f"Git SHA: `{result['git_sha']}`",
        f"n: `{result['n']}`",
        f"Replicates: `{result['replicates']}`",
        f"Clean populations: `{', '.join(result['clean_populations'])}`",
        "",
        "| constant | current | clean FPR | target rates | recommended |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for analysis in result["analyses"]:
        targets = ", ".join(
            f"{name}={rate:.1%}"
            for name, rate in analysis["current_target_rates"].items()
        )
        recommended = analysis["recommended"]
        if recommended is None:
            recommended_text = "none under FPR budget"
        else:
            recommended_text = (
                f"{recommended['threshold']:.4g} "
                f"(FPR {recommended['clean_fpr']:.1%}, "
                f"power {recommended['target_power_mean']:.1%})"
            )
        lines.append(
            "| "
            + " | ".join(
                [
                    analysis["constant"],
                    f"{analysis['current_threshold']:.4g}",
                    f"{analysis['current_clean_fpr']:.1%}",
                    targets,
                    recommended_text,
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def write_report(result: dict[str, Any], path: Path = REPORT_PATH) -> Path:
    path.write_text(render_markdown(result))
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    parser.add_argument("--n", type=int, default=DEFAULT_N)
    parser.add_argument("--base-seed", type=int, default=DEFAULT_BASE_SEED)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    result = analyze_thresholds(
        n=args.n,
        replicates=args.replicates,
        base_seed=args.base_seed,
    )
    if args.no_write:
        print(json.dumps(result, indent=2))
        return 0
    json_path = write_json(result)
    report_path = write_report(result)
    print(f"Wrote {json_path}")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
