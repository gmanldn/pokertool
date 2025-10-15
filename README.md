# PokerTool v29.0.0 — Advanced Poker Assistant

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
  summary: Enhanced enterprise documentation and comprehensive unit tests added
---
POKERTOOL-HEADER-END -->

PokerTool is a comprehensive, professional-grade poker analysis and automation toolkit. It features a robust GUI, advanced dependency management, multi-table support, and intelligent screen scraping capabilities.

**📊 Project Statistics:**

- **48,339** lines of production Python code across **114** modules
- **17,953** lines of comprehensive test code  
- **47,165** lines of JavaScript/TypeScript frontend code
- **300+ features** across core engine, GUI, ML, and analytics
- **19 dependencies** automatically validated and managed

**Latest Version:** v29.0.0 - Complete Dependency Validation & Robust GUI System  
**Release Date:** January 2025  
**Status:** Production Ready ✅  
**Architecture:** Modular, enterprise-grade, fully tested

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

### **🏆 Primary Method: Comprehensive Setup (Recommended)**

```bash
# The ONLY recommended way to launch PokerTool
python scripts/start.py

# This single command handles everything:
# • Validates all 19 dependencies
# • Installs missing packages automatically
# • Sets up virtual environment if needed
# • Resolves import conflicts
# • Launches robust multi-tab GUI
```

### **🔧 Advanced Setup Options**

```bash
# Virtual environment only
python scripts/start.py --venv

# Dependencies only (no GUI)
python scripts/start.py --python

# Full system validation
python scripts/start.py --self-test

# Launch GUI only (after setup)
python scripts/start.py --launch
```

### **⚡ Quick Validation**

```bash
# Check all dependencies
python src/pokertool/dependency_manager.py

# Alternative launchers (for development only)
python scripts/launch_gui.py  # Direct GUI (bypasses validation)
python tests/test_gui.py      # Minimal test interface
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
python scripts/start.py --all

# Validates all dependencies, installs missing packages,
# sets up virtual environment, and launches GUI
```

### **⚡ Quick Launch Options**

```bash
# Direct GUI (bypasses CLI conflicts)
python scripts/launch_gui.py

# Full setup + validation + launch
python scripts/start.py

# Minimal test interface
python tests/test_gui.py

# Dependency validation only
python src/pokertool/dependency_manager.py
```

### **🔧 Advanced Options**

```bash
# Setup virtual environment only
python scripts/start.py --venv

# Install Python dependencies only
python scripts/start.py --python

# Install Node.js dependencies only
python scripts/start.py --node

# Run comprehensive system test
python scripts/start.py --self-test

# Validate environment only
python scripts/start.py --validate
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

```text
📊 DEPENDENCY VALIDATION REPORT
Total dependencies: 19
✅ Available: 14 (All critical dependencies)
❌ Missing: 3 (Optional only - auto-installing)
⚠️  Errors: 0
⏭️  Skipped: 2 (Platform-specific)
🎉 All critical dependencies are available! PokerTool is ready to run.
```

---

## 📊 Screen Scraping

### **🎯 Advanced Screen Capture System**

PokerTool features intelligent screen scraping with Betfair-optimized detection:

```bash
# Enable screen scraper through GUI
python scripts/launch_gui.py
# Click "Screen Scraper" button in Autopilot tab

# Or validate scraper dependencies
python src/pokertool/dependency_manager.py
```

**Capabilities:**

- **Real-time table detection** - Continuously monitors for poker tables
- **OCR text recognition** - Extracts pot sizes, stack sizes, and player actions
- **Multi-table support** - Track up to 12 tables simultaneously
- **Betfair optimization** - Specialized detection for Betfair Exchange Games
- **Generic fallback** - Works with most major poker sites
- **Screenshot testing** - Built-in capture verification tools

**Dependencies Automatically Checked:**

- ✅ **mss** - Screen capture library
- ✅ **pytesseract** - OCR functionality  
- ✅ **opencv-python** - Computer vision processing
- ✅ **tesseract-ocr** - System OCR engine
- ✅ **Pillow** - Image processing

### **🗂 Baseline Library Ingestion**

Maintain high scraper fidelity by curating up-to-date UI baselines:

```bash
# Ingest a directory of annotated screenshots into the baseline library
python tools/ui_baseline_ingest.py screenshots/betfair --site betfair --recursive \
    --metadata capture_tool=obs build=2025.10

# Inspect the generated manifest and curated samples
open assets/ui_baselines/baseline_manifest.json
```

- **Automatic manifest generation** keeps CI dashboards aligned with available baselines.
- **Metadata enrichment** (`--metadata` / `--metadata-file`) tags stakes, themes, or capture tooling.
- **Raw captures preserved** in `assets/ui_baselines/raw_samples/` for audit and reprocessing.
- Fully compatible with the adaptive detector—new baselines appear without restarting services.

---

## 🛠 Development

### **Architecture & Code Quality**

- **Modular Design**: 114 Python modules with clear separation of concerns
- **Type Safety**: Comprehensive type hints across 48,339 lines of code
- **Error Handling**: Robust exception handling with graceful degradation
- **Testing**: 17,953 lines of test code ensuring reliability
- **Documentation**: Extensive docstrings and API documentation

### **Key Development Tools**

```bash
# 🧪 COMPREHENSIVE TEST SUITE (Recommended)
python tests/test_everything.py              # Run ALL tests with detailed logging
python tests/test_everything.py --verbose    # Verbose output with full details
python tests/test_everything.py --quick      # Quick tests only (no system tests)
python tests/test_everything.py --system     # System tests only
python tests/test_everything.py --coverage   # Run with coverage report

# Comprehensive system test
python scripts/start.py --self-test

# Dependency validation
python src/pokertool/dependency_manager.py

# Legacy test runner
python scripts/run_tests.py

# Code quality checks (when available)
python tools/poker_go.py --check-only
```

### **Comprehensive Test Suite**

PokerTool includes a comprehensive test runner that executes all 69+ test files and provides detailed logging:

```bash
# Run all tests with detailed logging
python tests/test_everything.py
```

**Features:**

- ✅ **Automatic test discovery** - Finds all test files across the project
- ✅ **Detailed logging** - Logs to both console and timestamped log files
- ✅ **JSON reports** - Machine-readable test results
- ✅ **Coverage reports** - Optional code coverage analysis
- ✅ **Flexible modes** - Quick, system, or comprehensive test runs
- ✅ **Color-coded output** - Easy-to-read results with status indicators

**Test Logs Location:** `test_logs/test_run_YYYYMMDD_HHMMSS.log`

**Sample Output:**
```text
================================================================================
POKERTOOL COMPREHENSIVE TEST SUITE
================================================================================
Timestamp: 2025-10-13 12:00:00
Log file: test_logs/test_run_20251013_120000.log
Mode: COMPREHENSIVE (all tests)
--------------------------------------------------------------------------------

Found 69 test files
Running pytest...
...
================================================================================
TEST SUMMARY
================================================================================
Total Tests Run:  245
✅ Passed:        238
❌ Failed:        3
⏭️  Skipped:       4
Pass Rate:        97.1%
```

### **Module Structure**

- **📁 src/pokertool/core/** - Core poker engine and hand analysis
- **📁 src/pokertool/modules/** - Screen scraping and specialized tools
- **📁 src/pokertool/enhanced_gui_components/** - GUI components and styling
- **📁 tests/** - Comprehensive test suite
- **📁 tools/** - Development and deployment utilities

---

## 📖 Documentation

### **Available Documentation:**

- **README.md** - This comprehensive overview
- **FEATURES.md** - Complete feature list with technical details
- **docs/** - Additional technical documentation
- **Inline Documentation** - Extensive docstrings throughout codebase

### **Getting Help:**

- **Built-in Diagnostics** - GUI includes diagnostic tools for troubleshooting
- **Dependency Validation** - Automatic checking and resolution guidance
- **Error Recovery** - Fallback systems with clear error messages
- **Debug Mode** - Enhanced debugging features throughout application

---

## 🤝 Contributing

### **Development Workflow:**

```bash
# Clone and setup
git clone https://github.com/gmanldn/pokertool.git
cd pokertool
python scripts/start.py --all  # Complete setup

# Make changes and test
python scripts/start.py --self-test  # Comprehensive validation
python scripts/run_tests.py          # Run test suite

# Create feature branch
git checkout -b feature/your-feature
git commit -m "Your changes"
git push origin feature/your-feature
```

### **Code Standards:**

- **Type Hints**: Required for all public APIs
- **Documentation**: Docstrings for all modules and functions
- **Testing**: Tests required for new features
- **Error Handling**: Graceful failure modes
- **Dependency Management**: Use the validation system
- **Markdown Formatting**: Lists must be surrounded by blank lines

### **Markdown Formatting Guidelines:**

**IMPORTANT**: All markdown lists must be surrounded by blank lines to ensure proper rendering and linting compliance.

**❌ Incorrect:**
```markdown
Some text here.
- Item 1
- Item 2
More text here.
```

**✅ Correct:**
```markdown
Some text here.

- Item 1
- Item 2

More text here.
```

**Tools:**

```bash
# Check markdown formatting
python -m pytest tests/test_markdown_formatting.py

# Fix markdown list formatting automatically
python scripts/fix_markdown_lists.py
```

### **Supported Contributions:**

- 🐛 Bug fixes and improvements
- ✨ New features and enhancements  
- 📖 Documentation updates
- 🧪 Test coverage improvements
- 🎨 UI/UX enhancements
- 🌍 Internationalization

---

## 📄 License

This project is released under the **Apache 2.0** license. See [LICENSE](LICENSE) for details.

---

## 🏆 Enterprise Features

### **Production Readiness:**

- ✅ **Zero-downtime deployment** capabilities
- ✅ **Professional error handling** with fallback systems
- ✅ **Comprehensive logging** and monitoring
- ✅ **Dependency validation** preventing runtime failures
- ✅ **Multi-platform support** (Windows, macOS, Linux)
- ✅ **Enterprise-grade architecture** with modular design

### **Performance Metrics:**

- **Startup Time**: < 3 seconds with full validation
- **Memory Usage**: ~200-500MB depending on features enabled
- **Thread Pool**: 20 concurrent threads for parallel processing
- **Table Detection**: < 20ms per scan cycle
- **Response Time**: < 100ms for most user interactions

**PokerTool v29.0.0** - Professional poker analysis platform with enterprise-grade reliability and comprehensive feature set.
