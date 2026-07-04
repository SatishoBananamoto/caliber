"""Tests for threshold operating-point analysis."""

import json

from lab import analyze_thresholds


def test_analyze_thresholds_shape_and_recommendations():
    result = analyze_thresholds.analyze_thresholds(
        n=30,
        replicates=5,
        sha="testsha",
    )

    assert result["git_sha"] == "testsha"
    constants = {analysis["constant"] for analysis in result["analyses"]}
    assert "LOW_UNCERTAINTY_THRESHOLD" in constants
    assert "DUPLICATE_RATIO_THRESHOLD" in constants
    for analysis in result["analyses"]:
        assert "current_clean_fpr" in analysis
        assert "current_target_rates" in analysis
        assert analysis["recommended"] is None or (
            analysis["recommended"]["clean_fpr"] <= 0.05
        )


def test_threshold_writers_emit_json_and_markdown(tmp_path):
    result = analyze_thresholds.analyze_thresholds(
        n=30,
        replicates=3,
        sha="testsha",
    )

    json_path = analyze_thresholds.write_json(result, tmp_path)
    report_path = analyze_thresholds.write_report(result, tmp_path / "THRESHOLDS.md")

    assert json.loads(json_path.read_text())["git_sha"] == "testsha"
    report = report_path.read_text()
    assert "Caliber Threshold Analysis" in report
    assert "LOW_UNCERTAINTY_THRESHOLD" in report
