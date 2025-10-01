"""Tests for the advanced reporting utilities."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.advanced_reporting import (
    ChartConfig,
    ReportBuilder,
    ReportRequest,
    ReportSection,
    ReportTemplate,
)


def create_builder(tmp_path: Path) -> ReportBuilder:
    storage = tmp_path / "reports"
    return ReportBuilder(storage_dir=storage)


def test_report_generation_with_template_and_pdf(tmp_path):
    builder = create_builder(tmp_path)
    template = ReportTemplate(
        template_id="performance",
        name="Performance Overview",
        description="Summary of player results",
        sections=[
            ReportSection(
                section_id="summary",
                title="Monthly Summary",
                content="Winrate steady with slight uptick.",
                chart=ChartConfig(chart_type="line", title="Winrate", x_label="Week", y_label="BB/100", colors=["#1f77b4"]),
            )
        ],
    )
    builder.register_template(template)

    custom_section = ReportSection(
        section_id="notes",
        title="Coach Notes",
        content="Focus on defending big blind versus steals.",
    )

    request = ReportRequest(template_id="performance", custom_sections=[custom_section], metadata={"author": "coach"})
    report = builder.build_report("Hero Performance", request)

    assert report.metadata["section_count"] == 2
    assert report.sections[0]["chart"]["chart_type"] == "line"
    path = builder.export_pdf(report)
    assert path.exists()
    saved_path = builder.save_report_json(report)
    assert saved_path.exists()

    builder.email_report(report, ["hero@example.com", "coach@example.com"])
    log = builder.delivery_log()
    assert len(log) == 1
    assert "hero@example.com" in log[0]["recipients"]


def test_numeric_series_summary():
    data = [5.0, 10.0, 15.0, 20.0]
    summary = ReportBuilder.summarize_numeric_series(data)
    assert summary["count"] == 4
    assert summary["mean"] == 12.5
    assert summary["median"] == 12.5
    assert summary["stdev"] == 5.59

    empty_summary = ReportBuilder.summarize_numeric_series([])
    assert empty_summary["count"] == 0
