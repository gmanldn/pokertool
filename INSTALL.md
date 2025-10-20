# Installation Guide

This document walks through installing PokerTool for local development or evaluation. If you only need a high-level overview, refer to `README.md`; the steps below provide the full workflow, platform-specific notes, and verification tips.

## Supported Platforms
- macOS 12+ (Intel or Apple Silicon)
- Ubuntu 20.04+ (or another recent Debian-based distribution)
- Windows 10/11 (PowerShell or Windows Terminal)

> PokerTool targets Python 3.10 – 3.13. Earlier interpreters are not supported because optional ML dependencies rely on newer CPython ABIs.

## Prerequisites
- Git 2.30 or later
- Python 3.10 – 3.13 with `pip` (`py -3.10` on Windows, `python3` everywhere else)
- Node.js 18 LTS (required for the React dashboard)
- Build essentials for native wheels  
  - macOS: Xcode command line tools (`xcode-select --install`)  
  - Ubuntu: `sudo apt install build-essential python3-dev`  
  - Windows: Install the "Desktop development with C++" workload from Visual Studio Build Tools
- System OCR dependencies (recommended)  
  - macOS: `brew install tesseract python-tk`  
  - Ubuntu: `sudo apt install tesseract-ocr python3-tk`  
  - Windows: Install [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) and ensure it is on `PATH`

## Quick Start (Automated)
The launcher script creates a Python virtual environment, installs backend/frontend dependencies, and starts both services.

```bash
git clone https://github.com/gmanldn/pokertool.git
cd pokertool
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python scripts/start.py --setup-only  # Install backend + frontend prerequisites
python scripts/start.py               # Launch API + React dashboard
```

When the startup finishes, open `http://localhost:3000` to use the dashboard. The backend API listens on `http://localhost:5001`.

### Running the self-test suite
Use the built-in diagnostics before first use or after upgrades:

```bash
python scripts/start.py --self-test
```

The self-test runs dependency validation, scraper smoke checks, and the standard unit test collection. Review `logs/errors-and-warnings.log` if any step fails.

## Manual Installation (Advanced)
If you prefer to manage dependencies manually, follow these steps instead of `start.py --setup-only`.

1. **Create and activate a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   Optional components (OCR, CV, ML) are listed in `requirements.txt`; remove entries you do not need before installing.

3. **Install frontend dependencies**
   ```bash
   npm install --prefix pokertool-frontend
   ```

4. **Build static assets (optional for production)**
   ```bash
   npm run build --prefix pokertool-frontend
   ```

5. **Start the services**
   ```bash
   # Backend API
   python -m pokertool web

   # Frontend (in a separate terminal)
   npm run start --prefix pokertool-frontend
   ```

## Verifying the Environment
- `python test.py --quick` – smoke tests without slow Betfair scenarios.
- `python test.py` – full validation pipeline (architecture graph refresh + unit/integration tests).
- `pytest tests/ -k scraper` – targeted scraper accuracy tests.
- Review the generated `logs/` directory; the consolidated file `logs/errors-and-warnings.log` should be empty after a clean run.

## Updating or Reinstalling
1. Pull the latest code (`git pull`).
2. Activate the virtual environment.
3. Re-run the setup command to pick up new dependencies:
   ```bash
   python scripts/start.py --setup-only
   npm install --prefix pokertool-frontend
   ```
4. Restart the services.

## Troubleshooting Tips
- Ensure Node.js 18+ is on `PATH` before running `start.py`; the script installs frontend dependencies via `npm`.
- If OpenCV or other native wheels fail to compile, install the platform build tools listed in the prerequisites.
- On Windows, run PowerShell as Administrator the first time so Tesseract and Python can update the registry.
- Use `scripts/monitor-errors.sh` for a consolidated view of backend warnings during development.

## Documentation
- Manual: docs/MANUAL.md
- Quick Reference: docs/QUICK_REFERENCE.md
- HUD Designer Guide: docs/advanced/hud.md
