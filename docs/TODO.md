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

### Consolidate JSON assets into canonical folder

- GUID: 909d0a54-a6cc-4a04-a4e2-e1b18fb8b082
- Type: operations
- Status: Open
- Components: Backend, Tooling
- Duplicate Guard: JSON files scattered across ranges/, docs/, tests/specs/, config roots; need central JSON folder plus enforcement test
- Created: 2025-10-18

JSON resources that drive ranges, architecture graphs, and spec fixtures currently live in dozens of
directories (ranges/, tests/specs/, docs/, exports/) which makes maintenance and import resolution
brittle. Centralising first-party JSON into a dedicated repository folder keeps asset discovery
predictable and prevents new files being dropped in arbitrary locations.

**AI Implementation Notes**

Define a canonical folder such as assets/json for project-owned data. Inventory existing JSON files,
separating first-party assets from third-party manifests like package.json that must remain in
place. Move the first-party files, update import paths and build scripts accordingly, and add a
pytest or scripts-based guard that asserts every non-vendor JSON under the repo resides in the
canonical folder. Update documentation so contributors know the new rule.

### Standardise PNG asset storage and validation

- GUID: a9424f9c-4028-4847-8afc-5199b0c52aaa
- Type: operations
- Status: Open
- Components: Frontend, Tooling
- Duplicate Guard: PNG screenshots and icons live in repo root/assets/docs; create dedicated png directory and test enforcement
- Created: 2025-10-18

PNG assets such as UI screenshots, debug captures, and documentation imagery are currently scattered
across the repository root and various docs folders, making it hard to manage updates or clean
obsolete files. We need a single canonical location for maintained PNGs so asset hygiene and
packaging automation stay reliable.

**AI Implementation Notes**

Create a top-level assets/png (or similar) directory and migrate curated PNGs there, updating
references in Markdown, tests, and code. Decide how to treat generated debug captures or historical
screenshots that should remain elsewhere, documenting any exceptions. Add an automated test that
scans the tree (excluding vendor caches) and fails when PNG files are committed outside the approved
directory. Update contributor docs with the new guideline.

<!-- TASKS_END -->

## Historical Backlog
The previous backlog (release histories and legacy checklists) now lives in `docs/TODO_ARCHIVE.md` for reference only.
