# PokerTool Formal Issue Register

> ⚠️ All issue entries in this register must be authored with `python new_task.py`. Manual edits beneath the task markers are prohibited so automated tooling can guarantee consistent metadata.

## Usage Policy
- Run `python new_task.py --help` for the full CLI. The helper enforces GUID allocation, required metadata capture, and Markdown formatting.
- Supply precise `--duplicate-guard` context (symptoms, log signatures, modules) so future contributors can spot potential duplicates.
- Provide a complete paragraph for both `--summary` (what and why) and `--ai-notes` (prescriptive remediation guidance). The script rejects single-sentence stubs.
- Status values are restricted to `Open`, `In Progress`, `Blocked`, `Needs Review`, or `Done` to standardise reporting.

### Required Metadata Fields
- **Title** – concise problem statement.
- **Type** – one of `bug`, `enhancement`, `research`, `doc`, `test`, or `operations`.
- **Status** – current lifecycle indicator.
- **Duplicate Guard** – canonical keywords, log snippets, or module names that uniquely identify this issue.
- **Summary Paragraph** – explain the problem impact and motivation.
- **AI Implementation Notes** – concrete guidance, acceptance criteria, or troubleshooting steps an AI assistant should follow.

## Active Issues

<!-- TASKS_BEGIN -->
<!-- No active issues recorded. Run `python new_task.py --help` to add one. -->
<!-- TASKS_END -->

## Historical Backlog
The previous backlog (release histories and legacy checklists) now lives in `docs/TODO_ARCHIVE.md` for reference only.
