"""Tests for the Phase 2 benchmark harness."""

import json

from lab import run_bench, simulate


def test_run_bench_shape_and_determinism():
    populations = {
        "honest": simulate.honest,
        "farmer": simulate.farmer,
    }
    first = run_bench.run_bench(
        replicates=3,
        sample_sizes=(20,),
        populations=populations,
        sha="testsha",
    )
    second = run_bench.run_bench(
        replicates=3,
        sample_sizes=(20,),
        populations=populations,
        sha="testsha",
    )

    first["generated_utc"] = second["generated_utc"]
    assert first == second
    assert first["git_sha"] == "testsha"
    assert len(first["rows"]) == 2
    assert first["rows"][0]["population"] == "honest"
    assert first["rows"][0]["replicates"] == 3
    assert "LOW_OUTCOME_VARIANCE" in first["rows"][0]["flag_rates"]


def test_bench_rates_capture_farmer_more_than_honest():
    result = run_bench.run_bench(
        replicates=8,
        sample_sizes=(100,),
        populations={
            "honest": simulate.honest,
            "farmer": simulate.farmer,
        },
        sha="testsha",
    )
    rows = {row["population"]: row for row in result["rows"]}

    assert rows["honest"]["any_flag_rate"] < rows["farmer"]["any_flag_rate"]
    assert rows["farmer"]["flag_rates"]["LOW_OUTCOME_VARIANCE"] > 0
    assert rows["farmer"]["flag_rates"]["CONFIDENCE_CONCENTRATION"] > 0


def test_writers_emit_json_and_markdown(tmp_path):
    result = run_bench.run_bench(
        replicates=2,
        sample_sizes=(20,),
        populations={"honest": simulate.honest},
        sha="testsha",
    )

    json_path = run_bench.write_json(result, tmp_path)
    report_path = run_bench.write_report(result, tmp_path / "REPORT.md")

    loaded = json.loads(json_path.read_text())
    assert loaded["git_sha"] == "testsha"
    report = report_path.read_text()
    assert "Caliber Adversarial Lab Benchmark" in report
    assert "| honest | 20 |" in report
