"""Comprehensive reporting utilities with templating, chart config, and delivery hooks."""

from __future__ import annotations

import json
import statistics
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

DEFAULT_REPORT_DIR = Path.home() / ".pokertool" / "reports"
DEFAULT_REPORT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ChartConfig:
    """Chart configuration metadata."""

    chart_type: str
    title: str
    x_label: str
    y_label: str
    style: str = "classic"
    colors: List[str] = field(default_factory=list)


@dataclass
class ReportSection:
    """Single section of a report."""

    section_id: str
    title: str
    content: str
    chart: Optional[ChartConfig] = None

    def render(self) -> Dict[str, Any]:
        payload = {
            "id": self.section_id,
            "title": self.title,
            "content": self.content,
        }
        if self.chart:
            payload["chart"] = self.chart.__dict__
        return payload


@dataclass
class ReportTemplate:
    """Reusable report template."""

    template_id: str
    name: str
    description: str
    sections: List[ReportSection]
    created_at: float = field(default_factory=time.time)


@dataclass
class ReportRequest:
    """Input for building a custom report."""

    template_id: Optional[str]
    custom_sections: List[ReportSection]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportResult:
    """Finalized report payload."""

    report_id: str
    title: str
    sections: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    created_at: float

    def to_json(self) -> str:
        return json.dumps({
            "report_id": self.report_id,
            "title": self.title,
            "sections": self.sections,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }, indent=2)


class ReportBuilder:
    """Core entry point for advanced reporting workflows."""

    def __init__(self, storage_dir: Path = DEFAULT_REPORT_DIR):
        self._storage_dir = storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._templates: Dict[str, ReportTemplate] = {}
        self._delivery_log: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Template management
    # ------------------------------------------------------------------
    def register_template(self, template: ReportTemplate) -> None:
        self._templates[template.template_id] = template

    def list_templates(self) -> List[ReportTemplate]:
        return sorted(self._templates.values(), key=lambda t: t.created_at)

    def get_template(self, template_id: str) -> Optional[ReportTemplate]:
        return self._templates.get(template_id)

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------
    def build_report(self, title: str, request: ReportRequest) -> ReportResult:
        sections: List[ReportSection] = []
        if request.template_id:
            template = self.get_template(request.template_id)
            if not template:
                raise KeyError(f"Unknown template: {request.template_id}")
            sections.extend(template.sections)
        sections.extend(request.custom_sections)
        if not sections:
            raise ValueError("Report must contain at least one section")
        rendered_sections = [section.render() for section in sections]
        report_id = f"report_{int(time.time() * 1000)}"
        metadata = dict(request.metadata)
        metadata.setdefault("section_count", len(rendered_sections))
        metadata.setdefault("generated_at", time.strftime("%Y-%m-%d %H:%M:%S"))
        return ReportResult(report_id=report_id, title=title, sections=rendered_sections, metadata=metadata, created_at=time.time())

    def export_pdf(self, report: ReportResult, filename: Optional[str] = None) -> Path:
        filename = filename or f"{report.report_id}.pdf"
        pdf_path = self._storage_dir / filename
        summary = textwrap.dedent(f"""
        REPORT: {report.title}
        CREATED: {report.metadata.get('generated_at')}
        SECTIONS: {report.metadata.get('section_count')}
        """)
        pdf_path.write_text(summary + report.to_json(), encoding="utf-8")
        return pdf_path

    def email_report(self, report: ReportResult, recipients: Iterable[str]) -> None:
        entry = {
            "report_id": report.report_id,
            "recipients": list(recipients),
            "sent_at": time.time(),
        }
        self._delivery_log.append(entry)

    def delivery_log(self) -> List[Dict[str, Any]]:
        return list(self._delivery_log)

    # ------------------------------------------------------------------
    # Analytics helpers
    # ------------------------------------------------------------------
    @staticmethod
    def summarize_numeric_series(series: List[float]) -> Dict[str, float]:
        if not series:
            return {"count": 0, "mean": 0.0, "median": 0.0, "stdev": 0.0}
        mean = statistics.fmean(series)
        median = statistics.median(series)
        stdev = statistics.pstdev(series)
        return {
            "count": len(series),
            "mean": round(mean, 2),
            "median": round(median, 2),
            "stdev": round(stdev, 2),
        }

    def save_report_json(self, report: ReportResult) -> Path:
        report_path = self._storage_dir / f"{report.report_id}.json"
        report_path.write_text(report.to_json(), encoding="utf-8")
        return report_path


__all__ = [
    "ChartConfig",
    "ReportBuilder",
    "ReportRequest",
    "ReportResult",
    "ReportSection",
    "ReportTemplate",
]
