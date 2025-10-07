        <!-- POKERTOOL-HEADER-START
        ---
        schema: pokerheader.v1
project: pokertool
file: README.md
version: v28.0.0
last_commit: '2025-09-23T12:55:52+01:00'
fixes:
- Merged duplicate root readmes into a single canonical README.md
- date: '2025-09-25'
  summary: Enhanced enterprise documentation and comprehensive unit tests added
        ---
        POKERTOOL-HEADER-END -->

# PokerTool v29.0.0 — Advanced Poker Assistant

PokerTool is a comprehensive, professional-grade poker analysis and automation toolkit. It features a robust GUI, advanced dependency management, multi-table support, and intelligent screen scraping capabilities.

**Latest Version:** v29.0.0 - Complete Dependency Validation & Robust GUI System  
**Release Date:** January 2025  
**Status:** Production Ready ✅

---

## Contents
- [🚀 Quick Start](#-quick-start)
- [🎯 Key Features](#-key-features)
- [📋 System Requirements](#-system-requirements)
- [💻 Installation Methods](#-installation-methods)
- [🎮 GUI Interface](#-gui-interface)
- [🔧 Dependency Management](#-dependency-management)
- [📊 Screen Scraping](#-screen-scraping)
- [🛠 Development](#-development)
- [📖 Documentation](#-documentation)
- [🤝 Contributing](#-contributing)

---

## 🚀 Quick Start

### **Method 1: Automatic Setup (Recommended)**
```bash
# Full setup with dependency validation
python start.py

# Or for direct GUI launch (fastest)
python launch_gui.py
```

### **Method 2: Manual Setup**
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies with validation
python start.py --python

# Launch GUI
python launch_gui.py
```

### **Method 3: Quick Test**
```bash
# Minimal test interface
python test_gui.py
```

---

## 🎯 Key Features

### **✅ Version 29.0.0 Improvements:**
- **🔍 Comprehensive Dependency Validation** - Validates all 19 dependencies upfront
- **🎮 Robust Multi-Tab GUI** - Error-resilient interface with fallback content
- **🛠 Enhanced Launch System** - Multiple launch methods with conflict resolution
- **📊 Real-time Screen Scraping** - Advanced table detection and analysis
- **🧵 Professional Threading** - 20-thread pool with proper management
- **💾 Smart State Management** - Clean separation of code and runtime data

### **Core Capabilities:**
- **Advanced Hand Analysis** - GTO solver with equity calculations
- **Multi-Table Support** - Manage up to 12 tables simultaneously
- **Screen Scraping** - Real-time table state detection (Betfair optimized)
- **Opponent Modeling** - ML-based opponent pattern recognition
- **Coaching System** - Integrated learning and improvement tools
- **Analytics Dashboard** - Session tracking and performance metrics
- **Gamification** - Achievement system and progress tracking
- **Community Features** - Forums, challenges, and knowledge sharing

---

## 📋 System Requirements

### **Supported Platforms:**
- ✅ **macOS** 10.15+ (Catalina and later)
- ✅ **Linux** (Ubuntu 18.04+, CentOS 7+, Fedora 30+)
- ✅ **Windows** 10/11

### **Dependencies Automatically Validated:**
- **Python 3.8-3.12** (Python 3.13 supported with limited features)
- **Critical:** numpy, opencv-python, Pillow, pytesseract, mss, requests
- **System:** tkinter, tesseract-ocr
- **Optional:** torch, scikit-learn, pandas, websocket-client
- **macOS:** pyobjc-framework-Quartz

### **System Tools:**
- **macOS:** `brew install python-tk tesseract`
- **Linux:** `apt install python3-tk tesseract-ocr`
- **Windows:** Usually included with Python

---

## 💻 Installation Methods

### **🏆 Recommended: Automatic Setup**
```bash
# Complete setup with dependency validation
python start.py --all

# Validates all dependencies, installs missing packages,
# sets up virtual environment, and launches GUI
```

### **⚡ Quick Launch Options**
```bash
# Direct GUI (bypasses CLI conflicts)
python launch_gui.py

# Full setup + validation + launch
python start.py

# Minimal test interface
python test_gui.py

# Dependency validation only
python src/pokertool/dependency_manager.py
```

### **🔧 Advanced Options**
```bash
# Setup virtual environment only
python start.py --venv

# Install Python dependencies only
python start.py --python

# Install Node.js dependencies only  
python start.py --node

# Run comprehensive system test
python start.py --self-test

# Validate environment only
python start.py --validate
```

---

## 🎮 GUI Interface

### **Enhanced Multi-Tab Interface:**
- **🎯 Autopilot Tab** - Automated play with real-time monitoring
- **🎮 Manual Play** - Manual poker analysis and decision support
- **📊 Analysis** - Hand analysis and statistical tools
- **🎓 Coaching** - Learning system with progress tracking
- **⚙️ Settings** - Configuration and preferences
- **📈 Analytics** - Session statistics and performance metrics
- **🏆 Gamification** - Achievements, badges, and progress
- **👥 Community** - Forums, challenges, and knowledge sharing

### **Key Features:**
- **Robust Error Handling** - Continues working even if some modules fail
- **Fallback Content** - Shows helpful error messages with retry options
- **Conditional Loading** - Only loads tabs for available systems
- **Diagnostic Tools** - Built-in troubleshooting and system information
- **Real-time Updates** - Live table monitoring and status updates

---

## 🔧 Dependency Management

### **Comprehensive Validation System:**
PokerTool v29.0.0 includes a sophisticated dependency management system:

```bash
# Run dependency validation
python src/pokertool/dependency_manager.py
```

**Features:**
- ✅ **19 dependencies validated** with detailed status reporting
- ✅ **Automatic installation** of missing packages
- ✅ **Platform-specific checking** (macOS Quartz, Linux packages, Windows compatibility)
- ✅ **Critical vs optional** dependency classification
- ✅ **JSON reporting** for debugging and system analysis
- ✅ **Version checking** and compatibility validation

**Sample Output:**
```
📊 DEPENDENCY VALIDATION REPORT
Total dependencies: 19
✅ Available: 14 (All critical dependencies)
❌ Missing: 3 (Optional only - auto-installing)
⚠️  Errors: 0
⏭️  Skipped: 2 (Platform-specific)
🎉 All critical dependencies are available! PokerTool is ready to run.
```
# PokerTool — Modular Poker Assistant

PokerTool is a modular toolkit for helping players make better live poker decisions. It combines a desktop GUI, core hand-eval/odds logic, table state helpers, and optional screen‑scraping utilities.

This README consolidates the content from the previous **`README.md`** and **`README 2.md`** into one canonical document.

---

## Contents
- [Key Capabilities](#key-capabilities)
- [Repository Layout](#repository-layout)
- [Quick Start](#quick-start)
- [GUI Usage](#gui-usage)
- [Screen Scraper (Optional)](#screen-scraper-optional)
- [Command Line](#command-line)
- [Configuration](#configuration)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Development Notes](#development-notes)
- [Contributing](#contributing)
- [License](#license)

---

## Key Capabilities
- **Core poker logic**: card/rank enums, hand parsing, equity/outs helpers, and situation advice.
- **GUI**: a single enhanced poker GUI with quick tips, ranges, and table input.
- **Self-healing utilities**: scan & auto-fix common syntax issues before launch.
- **Screen scraping** *(optional)*: setup to extract table state from supported UIs.
- **Test/validation harness**: integration and security validation tests.
- **Logging**: single rolling log for tests and validation with retention policy.

> Tip: keep **one** GUI (the enhanced GUI) enabled; remove/ignore legacy GUI entry points.

---

## Repository Layout

> **Note:** This reflects the public structure at the time of merging. Folders not listed are either generated or internal.

```
/assets/                    # images and static assets
/docs/                      # additional docs and walkthroughs
/tools/                     # launchers, scanners, build/check scripts
/tests/                     # unit/integration tests
/src/                       # application code (frontend/back-end helpers)
/webview-ui/ or /pokertool-frontend/  # frontend bundles (when present)
/standalone/                # runtime files & one-click starters
k8s/, scripts/, proto/, locales/      # infra and i18n
start.py                    # tiny wrapper to launch the tool
run_tests.py                # convenience runner for pytest suites
pokertool/modules/*         # standalone Python helpers (scraper, GUI upgrades, etc.)
forwardscripts/launch_pokertool.py   # main launcher (calls scanners, then GUI)
tests/system/               # legacy + integration tests
tests/system/poker_test.py, final_test_validation.py, test_* # tests
requirements*.txt           # Python deps
pyproject.toml              # packaging / tooling
```

### Key Python entry points
- `start.py` — small wrapper that delegates to the launcher.
- `forwardscripts/launch_pokertool.py` — orchestrates preflight checks then launches the GUI.
- `tools/`:
  - `code_scan.py` *(if present)* — scans repo and optionally autofixes.
  - `poker_go.py` — convenience launcher that can run a quick scan first.
  - `verify_build.py`, `git_commit_*.py` — CI/local helpers.
- `pokertool.modules.poker_screen_scraper` — optional live table capture.
- `poker_imports.py` — centralised safe imports/paths.

---

## Quick Start

1. **Create a virtualenv (recommended)**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   # For GPU-enabled PyTorch, install with official instructions:
   # pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   # Optional scraper extras
   pip install -r requirements_scraper.txt
   ```

3. **Run the launcher**
   ```bash
   python3 start.py
   # or, if you prefer the tools wrapper:
   python3 tools/poker_go.py
   # or launch the lightweight runner directly:
   python3 -m pokertool.modules.run_pokertool gui
   ```

4. **Run the test suite**
   ```bash
   python3 run_tests.py
   # target specific tests:
   python3 run_tests.py tests/system/test_hand_replay_system.py -k overlay
   ```

On first run, the launcher will (if enabled) perform a **quick code scan** to detect common syntax/import issues and attempt safe automatic fixes before starting the GUI.

---

## GUI Usage

- Launch the **Enhanced Poker GUI**.
- Enter hole cards, position, stack sizes, and any known table information.
- Use the tips panel to see recommended actions, hand class, and risk profile.
- Equity/outs helpers can be toggled in advanced view.
- A **Screen Scraper** button (when enabled) opens setup for live capture.

> The project aims to maintain **one** canonical GUI. If you see legacy GUI files, prefer the enhanced version and remove old launchers in future clean-ups.

---

## Screen Scraper (Optional)

If you intend to capture live table state:

1. Install scraper dependencies:
   ```bash
 pip install -r requirements_scraper.txt
  ```
2. Run the scraper setup:
  ```bash
  python3 -m pokertool.modules.poker_screen_scraper
  ```
3. Configure regions, OCR, and mappings as instructed in the on-screen prompts.

> Scraper support varies by environment and theme; treat it as **optional**.

---

## Command Line

Most workflows are encapsulated in **`forwardscripts/launch_pokertool.py`** and **`tools/poker_go.py`**.

Typical flags you may find useful:

```bash
# Run a fast syntax check/auto-fix (if available), then launch
python3 tools/poker_go.py --autofix --quick

# Only run sanity checks
python3 tools/poker_go.py --check-only
```

> Flags are subject to change as utilities evolve; run with `-h` to view current options.

---

## Configuration

- `poker_config.json` — runtime defaults (e.g., logging level, feature flags).
- `onnx_workaround_config.json` — optional ML/ONNX fixups.
- Environment variables may be read by some tools; check script headers for supported overrides.

---

## Testing

Run unit/integration tests from the repo root:
```bash
pytest -q
```

The repository also includes focused tests, e.g. GUI integration, scraper validation, and security checks (where present under `tests/` or top-level `test_*.py`).

---

## Troubleshooting

**Common launch problems**
- _“from __future__ import … must occur at the beginning”_: Ensure file headers are clean. The preflight scanner will attempt to fix this automatically.
- _SyntaxError in Enums or dataclasses_: Caused by attribute assignment in `Enum` members. Prefer standard `Enum` patterns; the auto-fixer mitigates common mistakes.
- _ImportError for symbols like `Card`/`analyse_hand`_: Confirm you are importing from the right module and that older modules haven’t overwritten newer ones.
- _ImportError for torch_: If torch fails to import or version check fails, ensure you have a compatible torch wheel installed (>=2.0.0,<3.0.0). The `activate_pokertool.sh` script will attempt to install it automatically. For GPU support, install from official PyTorch channels.

**Logs & retention**
- A unified log file is kept for tests/validation. Old entries older than **1 year** are automatically pruned by the maintenance task (when enabled).

---

## Development Notes

- Keep the **enhanced GUI** as the only user-facing GUI; deprecate others.
- Prefer **type hints** and **ruff/black** (or your configured linters/formatters).
- Run the **code scanner** before committing to catch trivial breakages.
- When adding a **new module**, document it with a header block:

```markdown
<!-- POKERTOOL-MODULE
name: <module-name>
path: <relative/path.py>
purpose: <short purpose>
public_api: [<symbols users import>]
dependencies: [<key internal deps>]
last_reviewed: <YYYY-MM-DD>
-->
```

This enables future tooling to aggregate module docs into the README.

---

## Contributing

PRs are welcome. Please:
- Run local tests and the scanner.
- Keep changes small and focused.
- Update this README and any relevant docs under `/docs` when adding features.

---

## License

This project is released under the **Apache 2.0** license. See [LICENSE](LICENSE) for details.
