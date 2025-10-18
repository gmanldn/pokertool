#!/usr/bin/env python3
"""
Utility script for managed creation of structured TODO entries.

All active issues must be appended via this script so that metadata such as
GUIDs, lifecycle state, and AI remediation notes remain consistent across the
repository.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
import textwrap
import uuid
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent
TODO_PATH = ROOT / "docs" / "TODO.md"
BEGIN_MARKER = "<!-- TASKS_BEGIN -->"
END_MARKER = "<!-- TASKS_END -->"
VALID_TYPES = {"bug", "enhancement", "research", "doc", "test", "operations"}
VALID_STATUS = {"Open", "In Progress", "Blocked", "Needs Review", "Done"}


class TaskError(RuntimeError):
    """Raised when the TODO register cannot be updated safely."""


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append a structured PokerTool issue entry to docs/TODO.md.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--title", required=True, help="Concise issue title.")
    parser.add_argument(
        "--type",
        dest="issue_type",
        choices=sorted(VALID_TYPES),
        required=True,
        help="Issue classification.",
    )
    parser.add_argument(
        "--status",
        choices=sorted(VALID_STATUS),
        default="Open",
        help="Lifecycle status.",
    )
    parser.add_argument(
        "--duplicate-guard",
        required=True,
        help=(
            "Context that distinguishes this issue from others "
            "(logs, modules, component names, failure signatures)."
        ),
    )
    parser.add_argument(
        "--summary",
        required=True,
        help="Full paragraph describing what the issue is and why it matters.",
    )
    parser.add_argument(
        "--ai-notes",
        required=True,
        help=(
            "Actionable paragraph that helps an autonomous agent resolve the issue "
            "(diagnostics, acceptance criteria, rollout steps)."
        ),
    )
    parser.add_argument(
        "--components",
        default="General",
        help="Comma-separated list of affected components or subsystems.",
    )
    parser.add_argument(
        "--guid",
        default=None,
        help="Optional GUID override (otherwise a UUIDv4 is generated).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the rendered entry without mutating docs/TODO.md.",
    )
    return parser.parse_args(argv)


def validate_env() -> str:
    if not TODO_PATH.exists():
        raise TaskError(f"TODO register missing: {TODO_PATH}")

    content = TODO_PATH.read_text(encoding="utf-8")
    if BEGIN_MARKER not in content or END_MARKER not in content:
        raise TaskError(
            "TODO register is missing task markers. Ensure docs/TODO.md matches the managed format."
        )
    return content


def ensure_paragraph(field_name: str, text: str, min_chars: int = 80) -> str:
    cleaned = text.strip()
    if len(cleaned) < min_chars or " " not in cleaned:
        raise TaskError(f"{field_name} must be a descriptive paragraph (>= {min_chars} characters).")
    return cleaned


def ensure_duplicate_guard(text: str) -> str:
    cleaned = text.strip()
    if len(cleaned) < 40:
        raise TaskError("Duplicate guard must be at least 40 characters long and include concrete identifiers.")
    return cleaned


def choose_guid(raw_guid: str | None, existing_content: str) -> str:
    if raw_guid:
        try:
            guid = str(uuid.UUID(raw_guid))
        except ValueError as exc:
            raise TaskError(f"Invalid GUID override supplied: {raw_guid}") from exc
    else:
        guid = str(uuid.uuid4())

    existing = set()
    for line in existing_content.splitlines():
        if line.startswith("- GUID:"):
            existing.add(line.split(":", maxsplit=1)[1].strip())

    if guid in existing:
        raise TaskError(f"GUID {guid} already exists in docs/TODO.md.")
    return guid


def render_entry(
    *,
    title: str,
    guid: str,
    issue_type: str,
    status: str,
    duplicate_guard: str,
    summary: str,
    ai_notes: str,
    components: str,
) -> str:
    created = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    summary_wrapped = textwrap.fill(summary, width=100)
    ai_notes_wrapped = textwrap.fill(ai_notes, width=100)

    entry_sections = [
        f"### {title}",
        "",
        f"- GUID: {guid}",
        f"- Type: {issue_type}",
        f"- Status: {status}",
        f"- Components: {components}",
        f"- Duplicate Guard: {duplicate_guard}",
        f"- Created: {created}",
        "",
        summary_wrapped,
        "",
        "**AI Implementation Notes**",
        "",
        ai_notes_wrapped,
    ]
    return "\n".join(entry_sections).strip() + "\n"


def insert_entry(existing_content: str, entry: str) -> str:
    before, after = existing_content.split(END_MARKER, maxsplit=1)
    placeholder = "<!-- No active issues recorded. Run `python new_task.py --help` to add one. -->"
    sanitized_before = before.replace(placeholder, "").rstrip()

    if not sanitized_before.endswith("\n"):
        sanitized_before += "\n"
    if not sanitized_before.endswith("\n\n"):
        sanitized_before += "\n"

    updated_before = f"{sanitized_before}{entry}\n"
    return updated_before + END_MARKER + after


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    content = validate_env()

    summary = ensure_paragraph("Summary", args.summary)
    ai_notes = ensure_paragraph("AI notes", args.ai_notes)
    duplicate_guard = ensure_duplicate_guard(args.duplicate_guard)
    components = args.components.strip() or "General"
    guid = choose_guid(args.guid, content)

    entry = render_entry(
        title=args.title.strip(),
        guid=guid,
        issue_type=args.issue_type,
        status=args.status,
        duplicate_guard=duplicate_guard,
        summary=summary,
        ai_notes=ai_notes,
        components=components,
    )

    if args.dry_run:
        print(entry)
        return 0

    updated = insert_entry(content, entry)
    TODO_PATH.write_text(updated, encoding="utf-8")
    print(f"Issue {guid} appended to {TODO_PATH.relative_to(ROOT)}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except TaskError as exc:
        print(f"new_task.py error: {exc}", file=sys.stderr)
        raise SystemExit(1)
