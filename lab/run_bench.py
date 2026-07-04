"""Run deterministic integrity-flag benchmarks over simulated populations."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from caliber.integrity import IntegrityReport
from lab import simulate


DEFAULT_SAMPLE_SIZES = (20, 50, 100, 300)
DEFAULT_REPLICATES = 500
DEFAULT_BASE_SEED = 1701
RESULTS_DIR = Path(__file__).parent / "results"
REPORT_PATH = Path(__file__).parent / "REPORT.md"

FLAG_CODES = (
    "LOW_OUTCOME_VARIANCE",
    "NO_DISCRIMINATION",
    "CONFIDENCE_CONCENTRATION",
    "SUSPICIOUSLY_PERFECT",
    "DOMAIN_CONCENTRATION",
    "DUPLICATE_CLAIMS",
    "INSTANT_VERIFICATION",
    "UNWITNESSED_HISTORY",
)


def git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _population_seed(base_seed: int, population_index: int, n: int, replicate: int) -> int:
    return base_seed + population_index * 1_000_000 + n * 1_000 + replicate


def run_bench(
    *,
    replicates: int = DEFAULT_REPLICATES,
    sample_sizes: Iterable[int] = DEFAULT_SAMPLE_SIZES,
    base_seed: int = DEFAULT_BASE_SEED,
    populations: dict[str, simulate.Simulator] | None = None,
    sha: str | None = None,
) -> dict[str, Any]:
    """Run the benchmark and return a serializable result object."""
    if replicates <= 0:
        raise ValueError("replicates must be positive")

    selected = populations or simulate.POPULATIONS
    sizes = tuple(sample_sizes)
    rows = []
    for population_index, (name, simulator) in enumerate(selected.items()):
        for n in sizes:
            flag_counts = {code: 0 for code in FLAG_CODES}
            any_flag_count = 0
            metric_sums: dict[str, float] = {}
            metric_counts: dict[str, int] = {}

            for replicate in range(replicates):
                seed = _population_seed(base_seed, population_index, n, replicate)
                records = simulator(n, seed)
                report = IntegrityReport.from_predictions(
                    name,
                    simulate.to_predictions(records),
                )
                codes = {flag.code for flag in report.flags}
                if codes:
                    any_flag_count += 1
                for code in codes:
                    flag_counts[code] = flag_counts.get(code, 0) + 1
                for metric_name in (
                    "uncertainty",
                    "resolution",
                    "top_bucket_share",
                    "domain_hhi",
                    "duplicate_claim_ratio",
                    "template_claim_ratio",
                    "import_share",
                    "instant_verify_share",
                    "mendel_p_low",
                ):
                    value = getattr(report, metric_name)
                    if value is not None:
                        metric_sums[metric_name] = metric_sums.get(metric_name, 0.0) + value
                        metric_counts[metric_name] = metric_counts.get(metric_name, 0) + 1

            rows.append(
                {
                    "population": name,
                    "n": n,
                    "replicates": replicates,
                    "any_flag_rate": round(any_flag_count / replicates, 4),
                    "flag_rates": {
                        code: round(flag_counts.get(code, 0) / replicates, 4)
                        for code in FLAG_CODES
                    },
                    "mean_metrics": {
                        name: round(metric_sums[name] / metric_counts[name], 4)
                        for name in sorted(metric_sums)
                    },
                }
            )

    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": sha or git_sha(),
        "replicates": replicates,
        "sample_sizes": list(sizes),
        "base_seed": base_seed,
        "flag_codes": list(FLAG_CODES),
        "rows": rows,
    }


def write_json(result: dict[str, Any], results_dir: Path = RESULTS_DIR) -> Path:
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / f"bench-{result['git_sha']}.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    return path


def render_markdown(result: dict[str, Any]) -> str:
    headers = ["population", "n", "any_flag", *FLAG_CODES]
    lines = [
        "# Caliber Adversarial Lab Benchmark",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        f"Git SHA: `{result['git_sha']}`",
        f"Replicates per cell: `{result['replicates']}`",
        f"Sample sizes: `{', '.join(str(n) for n in result['sample_sizes'])}`",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in result["rows"]:
        values = [
            row["population"],
            str(row["n"]),
            f"{row['any_flag_rate']:.1%}",
            *[
                f"{row['flag_rates'][code]:.1%}"
                for code in FLAG_CODES
            ],
        ]
        lines.append("| " + " | ".join(values) + " |")
    lines.append("")
    lines.append(
        "Rates are the share of deterministic seeded replicates where a flag fired."
    )
    return "\n".join(lines) + "\n"


def write_report(result: dict[str, Any], path: Path = REPORT_PATH) -> Path:
    path.write_text(render_markdown(result))
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    parser.add_argument(
        "--sample-size",
        dest="sample_sizes",
        type=int,
        action="append",
        help="Sample size to include; may be repeated. Defaults to 20,50,100,300.",
    )
    parser.add_argument("--base-seed", type=int, default=DEFAULT_BASE_SEED)
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Run the benchmark without writing JSON/Markdown artifacts.",
    )
    args = parser.parse_args(argv)

    result = run_bench(
        replicates=args.replicates,
        sample_sizes=args.sample_sizes or DEFAULT_SAMPLE_SIZES,
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
