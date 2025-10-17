# PokerTool

PokerTool is a web-based poker assistant that combines real-time table detection, equity analysis, and coaching tools behind a React + Python stack. It ships with automated setup, a hardened logging pipeline, and scripts for headless operation.

## Features

- Real-time hand analysis with opponent modeling and coaching prompts.
- Modern web interface with multi-table support and live WebSocket updates.
- Automated dependency validation and environment bootstrap scripts.
- Screen-scraping utilities for Betfair-optimized capture pipelines.
- Comprehensive logging, diagnostics, and architecture graph tooling.

## Prerequisites

- Python 3.8 – 3.13 (3.13 supported with limited features).
- macOS 10.15+, Ubuntu 18.04+, or Windows 10/11.
- Recommended system packages: Tesseract OCR and tkinter (`brew install python-tk tesseract`, `apt install python3-tk tesseract-ocr`).

## Installation

```bash
git clone https://github.com/gmanldn/pokertool.git
cd pokertool
python scripts/start.py --all
```

The installer validates dependencies, provisions the virtual environment, and prepares the web UI assets. Use `python scripts/start.py --help` for advanced options.

## Quick Start

```bash
# Launch the web interface
python -m pokertool web

# Run the comprehensive test suite with architecture validation
python test.py

# Execute headless screen scraping (optional)
python -m pokertool scrape
```

Additional commands:

- `python scripts/start.py --self-test` — full system validation.
- `python src/pokertool/dependency_manager.py` — dependency health check.
- `pytest tests/ -v` — direct pytest access.

## Logging

Centralized logs live in `logs/`:

- `logs/errors-and-warnings.log` — aggregated errors and warnings (refresh with `./scripts/monitor-errors.sh`).
- `logs/pokertool_errors.log` — JSON error records with stack traces and runtime state.
- `logs/pokertool_master.log` — rolling backend activity stream.

Use `./scripts/error-summary.sh` to generate grouped error reports. See `logs/README.md` for the full troubleshooting workflow and retention policy.

## Documentation

- `FEATURES.md` — detailed feature grid.
- `docs/` — architecture, deployment, and integration guides.
- `GRAPHDATA.md` — architecture graph schema and tooling.
- `logs/README.md` — centralized logging playbook.

Release notes live in `CHANGELOG.md`, and `VERSION` tracks the current build tag.

## Contributing

Contributions are welcome. Review `CONTRIBUTING.md`, follow the coding standards, and run `python test.py` before opening a pull request. Issues and feature requests can be filed through the GitHub issue tracker.

## License

PokerTool is released under the Apache License 2.0. See `LICENSE` for details.

