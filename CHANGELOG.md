# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [87.0.1] - 2025-10-16


### 🧹 Chores

- Clean up repository cruft and update gitignore (0bb16fa7)

### Other Changes

- Merge release/v87.0.0 into develop (2c20d24b)

## [87.0.0] - 2025-10-16


### 🚀 Features

- Add comprehensive smoke test suite v87.0.0 (b51c2b4d)

## [86.3.0] - 2025-10-16


### ✅ Tests

- Add comprehensive React unit tests for all dashboard components (ecd54eea)

## [86.2.0] - 2025-10-16


### 🚀 Features

- Add routing and navigation for new ML feature dashboards (11c23338)
- Add three new frontend dashboards for ML feature visualization (eb4f2820)
- Add API endpoints for Sequential Opponent Fusion, Active Learning, and Scraping Accuracy (02396ba0)

## [86.1.0] - 2025-10-16


### 🐛 Bug Fixes

- Update health check imports to match existing module names (7f1ccd91)

### ✅ Tests

- Add comprehensive unit tests for system health checker (24f02d3a)

## [86.0.0] - 2025-10-16


### 🚀 Features

- Add launch scripts, app icon, and additional documentation (90b940a0)
- Add frontend configuration system for API endpoints (e3fe1d26)
- Add Model Calibration, Session Clock, and UI enhancements (5b1c9901)
- Complete System Status Monitor with comprehensive health checks (88379a2f)
- Implement comprehensive System Health Monitor v86.0.0 (d189e103)
- Create comprehensive system health checker service (3a6d501c)
- Add System Status routing to App.tsx (2895c124)
- Add System Status menu item to Navigation (858af3e6)
- Create SystemStatus.tsx component for real-time health monitoring (66fbc42f)
- Add Start Backend button to top navigation bar (b57610ec)

### 🐛 Bug Fixes

- Improve WebSocket connection handling in DetectionLog (9d66e891)
- TypeScript type assertions in DetectionLog component (5fe01aa0)

### 📚 Documentation

- Add comprehensive documentation for v86.0.0 features (289be2cd)
- Add CRITICAL System Status Monitor feature specification to TODO.md (c63118d4)

## [85.0.0] - 2025-10-16


### 🚀 Features

- Real-time detection WebSocket integration - v85.0.0 (a2b03ab5)
- **frontend**: Add Session Performance Dashboard component (WEB-UX-005) (b5bb2bce)
- **web**: Add Quick Settings Panel (WEB-UX-004) (ea5f76a1)
- **web**: Add keyboard shortcuts system (WEB-UX-003) (12a4d5fc)
- **web**: Add DecisionTimer component with alerts (WEB-ADVICE-008) (ab020022)
- **web**: Add OpponentStats component for opponent tendency tracking (WEB-ADVICE-007) (2123d914)
- Release v78.0.0 - Redux State Management & Mobile Responsive UI (5caa1344)
- Complete WEB-ADVICE-004 and WEB-UX-002 (d4228ae0)

### 🐛 Bug Fixes

- Correctly parse European decimal format (comma as decimal separator) for euro cent values (0c7220b1)

### 🧹 Chores

- bump version to 84.0.0 (ae193f76)

### Other Changes

- cmd (1cde7ab8)
- cmt (a8a57d54)
- cmt (e8b3a851)
- dev commit (969ccbe7)
- todo (1e990647)
- Documentation updates for v83.0.0 web-only architecture (3f25203e)
- Release v83.0.0: Complete tkinter removal and web-only architecture (68a8f0cb)
- v82.0.0: Complete Web Improvements & TODO Consistency (2e928933)
- Add comprehensive pot/bet detection analysis documentation (6ccdc356)
- Fix live card detection display - show hole cards and board cards in real-time (ff505c43)
- Fix table display to show real detection data instead of placeholder (1ac2c568)
- Fix pot/bet detection for micro stakes and European currency format (a70a388a)
- Implement persistent tracking with detection indicators and DetectionLog tab (ad3fd83e)
- Add remaining uncommitted files for v81.0.0 (ef95520f)
- Release v81.0.0: Comprehensive GUI Enhancement Suite (9da6b505)
- Release v80.0.0: Smart Advice Integration & Frontend Cleanup (c09799c5)
- cmt (a338ced3)
- Merge release/v76.0.0 into develop (17f2aa00)

## [76.0.0] - 2025-10-15


### 🚀 Features

- **web**: implement v76.0.0 web interface improvements - 5 core components (162262c0)
- Add component-level version tracking to VERSION file (0ef6a3f3)
- Implement all 35 scraping improvements for v75.0.0 (dbf3f854)

### 📚 Documentation

- Add v76.0.0 release notes (b7d234ae)
- Update TODO.md to mark all 35 scraping improvements as COMPLETED (f2e57038)

### 🧹 Chores

- improve state data management and project structure (59b38d13)

### Other Changes

- Merge release/v76.0.0 into main (4d78fe6c)
- Add ROI tracker implementation with tests (5cf6c2d5)
- Release v74.0.0: Repository cleanup and reorganization (fc554919)
- Enforce mandatory OCR engine availability (e24841a5)
- Analyze BF_MOVIE.mp4 for training data (8654d0a6)
- mov (4821963d)
- Release v73.0.0: Betfair-style visual updates to table tab (95c6f5dd)
- Fix Betfair player name and stack detection with inverted OCR preprocessing (dfb71df3)

## [72.0.0] - 2025-10-15


### Other Changes

- v72.0.0: Live Table Revolution - Complete data pipeline fix (6101ced6)
- Fix critical bug: Initialize _latest_state in create_scraper() (658da44d)
- Update version to v71.0.0 (87c4d940)

## [71.0.0] - 2025-10-15


### Other Changes

- Release v71.0.0 - GUI Performance Revolution (8d4378cd)
- Release v70.0.0 - Performance Powerhouse (9d04b681)
- Fix splash screen to show current version v69.1.0 (52a8beb0)

## [69.1.0] - 2025-10-15


### Other Changes

- Release v69.1.0: Automatic Chrome Connection - Zero Configuration (1e09f7b4)

## [69.0.0] - 2025-10-15


### Other Changes

- Release v69.0.0: Reliability & Resilience - High-Impact Improvements (72828850)

## [68.0.0] - 2025-10-14


### Other Changes

- Release v68.0.0: Process Management - kill.py Utility (a2d804b2)

## [67.0.0] - 2025-10-14


### 🚀 Features

- Add comprehensive telemetry instrumentation to core modules (09573bec)
- Add comprehensive performance telemetry system for GUI responsiveness analysis (e8791b55)

### 🐛 Bug Fixes

- Implement responsive startup with async module loading to prevent beach balling (21693926)

### Other Changes

- Release v67.0.0: Performance & Responsiveness - 7 Major Optimizations (71a4f65b)
- Add separate dock icons for main and compact windows on macOS (eeb37b2c)

## [66.0.0] - 2025-10-14


### Other Changes

- Release v66.0.0: Major Explanation System Enhancements (07e3e0af)

## [65.0.0] - 2025-10-14


### 🐛 Bug Fixes

- Re-enable LiveTable updates with thread-safe implementation (301f3f83)

### Other Changes

- Release v65.0.0: Detailed Explanation Textbox for LiveTable (d17a9905)
- Enhance status bar with rolling game state display & update to v64.0.0 (c1eea8e3)

## [64.0.0] - 2025-10-14


### Other Changes

- Release v64.0.0: Win Rate & Accuracy Optimization (c2612f93)

## [63.0.0] - 2025-10-14


### 🐛 Bug Fixes

- Pass parent window to CompactLiveAdviceWindow to prevent crash (26a0c15b)

### Other Changes

- Release v63.0.0: Python 3.13 Compatibility & UI Optimization (68472f35)
- Release v63.0.0: Dual Window UX & Data Quality (d941a2a7)
- Disable handle popup dialog on LiveTable startup (48249fc8)
- Add GameHistory Blade - Live Table Data Logger (57b8775a)
- Compact Live Advice Window: 18 High-Impact Enhancements (61249579)

## [62.0.0] - 2025-10-14


### 🚀 Features

- Add profile system and historical performance tracking (9f0edbfa)
- Add high-impact UI enhancements for information delivery and feedback (770eed02)
- Add circular UI element clustering for button detection (a8ae4581)
- Implement adaptive detection threshold auto-tuning (2b52d3f1)
- Add temporal consistency checks across frames (42e820c2)
- Add multi-scale detection for different resolutions (1cca1806)
- Implement incremental update detection (d4e0c0cd)
- Optimize contour detection with hierarchical analysis (4ef3ea1e)
- Parallelize multi-region OCR extraction with ThreadPoolExecutor (7ac48629)
- Enhanced smart ROI caching with perceptual hashing and adaptive TTL (3f3f3556)
- Add performance optimizations for faster extraction (b77ee9ad)
- Implement poker domain validation rules (07ea8f27)
- Add character-level confidence analysis for OCR validation (9471c12d)
- OCR ensemble integration and adaptive strategy selection (49dfca20)
- Advanced OCR improvements for maximum accuracy (f45ba3d1)
- Major screen scraping robustness and accuracy improvements (1462cf7e)
- Fix GUI disappearing + Add detection status lights panel (695eaeb9)
- Integrate learning system into start.py for automatic initialization (8e67cab8)
- Major learning system enhancements - active strategy application and smart caching (0eb6649b)
- Add comprehensive adaptive learning system for screen scraper (1cdd3c4e)

### 🐛 Bug Fixes

- Clean quit and data capture list index errors (30d312f2)

### 📚 Documentation

- Add comprehensive UI improvements documentation (497b883e)
- Organize all learning system documentation into docs folder (5d0abe15)
- Add comprehensive automatic learning user guide (3d3dc349)
- Add comprehensive V2 improvements documentation (f3716810)

### Other Changes

- Release v62.0.0: Enterprise Power Pack - 30 High-Impact Improvements (e6b6831d)
- Release v61.0.0: Compact Live Advice Window - Always-On-Top Real-Time Poker Assistant (81ab48c5)
- Release v60.0.0: Canonical version tracking system with release branch workflow (35b31455)
- Release v49.0.0: Comprehensive Screen Scraping Optimizations (35 Improvements) (4ae2a91f)
- Release v37.0.0: Complete UI enhancement integration + Screen scraping optimizations (2b60450c)
- Release v36.0.0: Critical GUI startup fixes (5b5f6bb2)

## [59.0.0] - 2025-10-13


### 🚀 Features

- Major OCR improvements and comprehensive validation for ALL critical data (416df67f)

### 🐛 Bug Fixes

- Critical OCR and card detection improvements for high-resolution images (876d4670)

## [58.0.0] - 2025-10-13


### 🚀 Features

- Add Chrome DevTools Protocol integration and comprehensive LiveTable enhancements (6a89d589)

### Other Changes

- Merge branch 'feature/chrome-devtools-table-enhancement' into develop (d00b0977)

## [57.0.0] - 2025-10-13


### Other Changes

- Release v57.0.0: Add diagnostic and testing utilities for Betfair scraper (fc12a9c0)

## [56.0.0] - 2025-10-13


### Other Changes

- Release v56.0.0: Fix LiveTable player data display with cached state optimization (4711d864)

## [55.0.0] - 2025-10-13


### 🚀 Features

- Implement continuous live table updates with data caching (08798a0a)

### 🐛 Bug Fixes

- Enhanced Betfair poker table detection (03cb03f3)

### Other Changes

- Fix screen scraping: Add smart poker detector with URL-based prioritization (f3189908)
- commit new (71d811d9)
- Fix validation error and display update crash (f7d31153)
- Release v54.0.0: Enhanced table detection with live validation and optimized OCR (a26d7935)

## [53.0.0] - 2025-10-13


### Other Changes

- Release v53.0.0: Fix pytest collection warnings and add testing documentation (a338ffd9)

## [52.0.0] - 2025-10-13


### Other Changes

- Release v52.0.0: Comprehensive Testing Infrastructure (d2647540)
- Release v51.0.0: CI Test Import Fixes (71942095)

## [51.0.0] - 2025-10-13


### Other Changes

- Fix CI test import errors: Add missing GTO deviation classes and fix module imports (20361025)

## [50.0.0] - 2025-10-13


### Other Changes

- Performance optimization: Enhanced database operations in active learning (e5f0957e)
- Clean up repository: Remove backup folders and large log files (5bf90132)

## [49.0.0] - 2025-10-13


### Other Changes

- Release v49.0.0: Repository Organization & Active Learning (974160a2)

## [48.0.0] - 2025-10-13


### Other Changes

- Release v47.0.0: Synthetic Scrape Data Generator (7d322d62)
- Release v46.0.0: Automated Scrape QA Harness (95f7b59b)
- Release v45.0.0: GPU Accelerated Preprocessing Pipeline (db4ed88d)

## [44.0.0] - 2025-10-13


### Other Changes

- Release v44.0.0: Sequential Opponent State Fusion with Transformer (14740c67)

## [43.0.0] - 2025-10-13


### Other Changes

- Release v43.0.0: Critical Performance & UX Improvements (c0c24481)

## [42.0.0] - 2025-10-13


### Other Changes

- Release v42.0.0: Real-Time Model Calibration and Drift Correction (8ade8408)

## [41.0.0] - 2025-10-13


### Other Changes

- Complete SCRAPE-012: OCR Ensemble and Validator (v41.0.0) (26db3bd6)
- Update TODO.md with completed v36-v40 tasks (10a2ae7f)
- Add comprehensive ADVERT.md documenting all features (2bfa3c26)

## [40.0.0] - 2025-10-12


### 🐛 Bug Fixes

- Add missing FONTS and COLORS definitions for hand history tab (160669ff)

### Other Changes

- Release v40.0.0: Auto-Integrated GTO & Compact UI (fc5f38c8)
- Add BF_TEST.jpg test image for purple table detection reference (54642faf)

## [39.0.0] - 2025-10-12


### Other Changes

- Release v39.0.0: Enhanced Hand History with Auto-Recording & Advanced Analytics (220b50db)
- Add comprehensive release notes for v38.0.0 (a63dfe2c)

## [38.0.0] - 2025-10-12


### Other Changes

- Release v38.0.0: Comprehensive Hand History System with GUI Tab (72b0f8fb)

## [37.0.0] - 2025-10-12


### Other Changes

- Release v37.0.0: Poker Handle Config + macOS OpenCV Fix (83315016)
- Add poker handle configuration for accurate hero detection (0e8eede5)

## [36.0.0] - 2025-10-12


### Other Changes

- Release v36.0.0: Purple Table Detection & Enhanced Startup Validation (aaca4e2a)

## [35.0.0] - 2025-10-12


### Other Changes

- Release v35.0.0: Confidence-Aware Decision API with Uncertainty Quantification (dfc816ed)

## [34.0.0] - 2025-10-12


### 🚀 Features

- Complete GTO-DEV-001 and mark all TODO tasks complete (982cfc72)
- Add comprehensive bootstrap scripts for all platforms (bde122a4)
- add GTO deviation engine and integrate with solver API (b8ea702c)

### 🐛 Bug Fixes

- Remove sys.path manipulation causing numpy import errors (ab0d3097)
- v20.2.0 - GUI tab visibility guaranteed + auto-start screen scraper + thread-safe services (2f83767b)
- Use native macOS 'aqua' theme for better tab visibility + explicit Notebook styling (ca313aa7)
- Disable background threads that cause Tcl/Tk segfaults + add direct system Python launcher (d2bd0eea)
- Revert forced UI updates that caused Tcl/Tk segfault - tabs building but visibility issue remains (57323682)
- Immediate quit functionality with os._exit(0) and force tab display with update_idletasks() (55ddf1e1)
- Skip slow optional dependencies (torch, easyocr, paddlepaddle) during auto-install to speed up launch from 5+ minutes to 5 seconds (d7ac17b6)
- Clean PYTHONPATH setup without appending to existing paths to resolve numpy import conflict (d7047378)
- Also remove ROOT from setup_python_path to fully resolve numpy import conflict (8ecf7cf5)
- Remove ROOT from PYTHONPATH to resolve numpy import conflict (f624a9d6)
- Skip slow optional dependencies during auto-install validation (8f8f6e51)
- Correct Suit enum case in fallback definition (v20.0.1) (d21c3633)
- **pokertool**: use autopilot panel state start_time to avoid AttributeError in _start_autopilot (8a3321ca)
- set button text color to black for improved readability on home screen (1eb7037c)

### 📚 Documentation

- update headers to v28.1.0 across all documentation (5943a1f1)
- normalise README encoding + create lightweight root README; move full guide to docs/ (01cf42fc)

### ♻️ Code Refactoring

- move remaining refactoring documentation to docs/refactoring/ (002359be)
- Fix nested package structure and corrupted files (de6abce7)
- tidy root python layout (71770e37)
- **shared**: move mistral provider data to module (8ba97495)
- **shared**: extract doubao provider metadata (58fbdd64)
- **shared**: isolate qwen provider metadata (543942fe)
- **shared**: modularize gemini provider metadata (473ccaf3)
- **shared**: extract openrouter metadata module (fd44ec14)
- **shared**: move vertex provider metadata to module (805dfad8)
- **shared**: separate bedrock provider metadata (6d2d68f1)
- **shared**: extract claude code provider metadata (70bf1c35)
- **shared**: modularize anthropic provider metadata (ee87cd1d)
- **shared**: extract API base types module (5a36d903)
- streamline screen scraping pipeline (fe9f95fc)

### 🧹 Chores

- enhance PyTorch installation robustness with version checks, documentation updates, and test (360fa337)
- improve accessibility — high contrast buttons and bold interface text (a9079d43)
- automate frontend deps and ml test guard (4074dccb)
- remove cruft and optimize opponent stats (85b49e30)

### Other Changes

- Release v34.0.0: Enhanced UX with Clear Hero Position & Auto Detection (86aa50b2)
- Update TODO.md with STARTUP-001 completion (f960c556)
- Add comprehensive startup validation system v33.0.0 (ee5b0443)
- Release v32.0.0: Modern UI with Real-Time Logging Tab (35ca334c)
- Make screen scraper ALWAYS-ON with comprehensive error logging (4ef669f6)
- Release v31.0.0: LiveTable Graphical Poker Table & UI Improvements (22e82756)
- Make all button text black and add graphical poker table to LiveTable (249e73de)
- Add missing accent_info color to style.py (54467be1)
- Enhanced LiveTable with complete real-time scraper integration (2a56e60d)
- save (f6fcff71)
- Release v30.0.0: Enhanced GUI with Screen Scraper Optimization (072d4045)
- Major codebase cleanup: Remove duplicate files and redundant code (ce00c57b)
- release 21 (5ab56a0a)
- Merge release/v21.0.0 into develop (1bcce082)
- Release v21.0.0 - Enhanced GUI (47941db1)
- dep (8d4e1285)
- start (063a219b)
- Fix enhanced GUI blade navigation crash (6e7317dc)
- Improve GUI blade navigation and optional torch support (badd37a6)
- Ensure launcher runs new GUI checks (e74fad89)
- Keep enhanced GUI tabs visible with scraper watchdog (94b0d5f1)
- Ensure enhanced GUI uses numpy guard (78d86aaa)
- Update dependency stack for TensorFlow and Paddle (188290eb)
- Enforce single-instance GUI and sync workspace snapshot (35ae7be2)
- Add new simple GUI with sidebar navigation (25853c12)
- Remove conflicting pokertool directory at project root (07fd386b)
- Fix numpy import conflicts with direct launcher script (95e12852)
- Remove torch_compat_stub to prevent numpy import conflicts (2e6f47eb)
- Improve numpy import reliability for GUI launch (8bf374fe)
- Add visualization packages and fix numpy import conflicts (ce2efc7a)
- Merge feature/gui-blade-fix-v20.2.0 into develop (e7317b52)
- Update dependency report, start.py changes, and add quick_start_gui.sh (987ef6e9)
- Update dependency report after numpy import fix validation (d170e426)
- Merge release/v3.30.4 back into develop (52586f0a)
- Bump version to 3.30.4 (ad010496)
- Fix syntax error: add missing # to comment on line 717 in adaptive_ui_detector.py (712f0a2d)
- Fix syntax error in adaptive_ui_detector.py - complete logger.info() statement on line 764 (dc1d0e60)
- Implement adaptive UI detection and multi-table segmenter (81ab1b25)
- new (7ce94082)
- Final enhancements: torch fallbacks, reduced debug output, definitive launcher (8a838f40)
- Enhanced documentation with accurate metrics and detailed features (49704ed4)
- Comprehensive documentation update for v29.0.0 (2611af5a)
- Major Update: Complete dependency validation and robust GUI system (f9d99543)
- Implement optimal multi-tab layout with configuration defaults (0dacd0ef)
- Fix all GUI import errors and create missing tab modules (2a4e59cc)
- Fix Python compatibility issues and dataclass slots support (9abbdbcc)
- Fix torch dependency issue: Remove torch.Tensor type annotation causing import errors (60c06d0e)
- Implement top 2 TODO tasks: SCRAPE-010 Adaptive UI Detection & SCRAPE-011 Multi-Table Segmenter (fc680f85)
- Capture blind and dealer seats in Betfair screen scraper (98941606)
- todo (ada3c261)
- Add torch/easyocr deps and create debug loop script (d0c27e48)
- Refine bootstrap to handle optional deps and default GUI (69df313a)
- Restore core module and guard CLI when Tk is missing (45d978dc)
- refactor (cfe6dc31)
- spades issue (dd361ca5)
- Oct_03_Early_new (828ff64e)
- ignore (cc4d869a)
- new (ac9fa32c)
- newoct_start (ff7b437d)
- cmt_2Oct_new (47a0a49c)
- Experimental (ebcdeed2)
- start (5a594f9c)
- start changes (e45f2356)
- saves_new (18b0e5f2)
- update to ignore (226fd0dd)
- update (1bedca9b)
- card recs (a1edaa31)
- scraper new version (f09ca603)
- scraper (394e5c5b)
- cmt (aa5eed64)
- scrape (67022060)
- late (5ff1bcc9)
- cmt (47de50ce)
- fixes (6cc9cd49)
- Merge branch 'develop' of https://github.com/gmanldn/pokertool into develop (7796a9c0)
- Merge pull request #20 from gmanldn/main (5d98f699)
- Merge pull request #19 from gmanldn/develop (d6e3a1f6)
- Fix PokerTool initialization errors (6c14b9bb)
- log (2ee19860)
- bugs (b909383f)
- gemini robust (3cf307ac)
- new gemini code (25a965c7)
- Merge pull request #18 from gmanldn/develop (86562ff2)
- Fix syntax errors reported in [master_log.txt](http://_vscodecontentref_/1) (placeholder fixes for generic errors) (7daa528c)
- Fix syntax errors reported in [master_log.txt](http://_vscodecontentref_/1) (placeholder fixes for generic errors) (8634bcca)
- gi (b9790832)
- chNGES (af1abfb6)
- Fix Suit import fallback and suit enumeration in poker_screen_scraper (3ded8fbd)
- Fix plus notation, grid initialization, and grid auto-refresh on add_range_string (d0edb46a)
- Release Version 28: Fixed test syntax errors and updated version numbers (fcbf51c4)
- Add comprehensive screen scraping refinements and performance optimizations (3e9fbda7)
- Implement desktop-independent screen scraping without Chrome dependencies (6149d161)
- Implement comprehensive master logging system with enhanced error capture (35fc125a)
- Implement SOLVER-API-001 and ENSEMBLE-001: Real-Time Solver API and Ensemble Decision System (e108a5f9)
- Implement META-001 and PREFLOP-001: Meta-Game Optimizer and Preflop Charts (0f111d7a)
- Complete TIMING-001 and STATS-001 tasks (f2427d10)
- Implement TIMING-001 and STATS-001: Timing Analyzer and Statistical Validator (a891dfa0)
- Update TODO.md: Mark MERGE-001 and QUANTUM-001 as completed (9fcb25ba)
- Complete MERGE-001 and QUANTUM-001: Advanced Range Merging and Quantum-Inspired Optimization (8b04ac34)
- Implement TIMING-001 and META-001: Timing Analyzer and Meta-Game Optimizer (d444a70a)
- Implement MERGE-001 and QUANTUM-001: Advanced Range Merging and Quantum Optimization (ee00b6bb)
- Complete BAYES-001 and RL-001: Mark tasks as completed in TODO.md (e95b96ae)
- Fix NumPy deprecation warning in RL Agent value network (65edf1b6)
- Implement BAYES-001 and RL-001: Bayesian Opponent Profiler and RL Agent (958e286b)
- Implement BAYES-001 and RL-001: Bayesian Opponent Profiler and RL Agent (6d0b979f)
- Complete MCTS-001 and ICM-001: Mark tasks as completed in TODO.md (9a091774)
- upd (4a8b8304)
- save off feature file (aa690ee3)
- Further todo updates (d07972b3)
- TODO tasks done (4407cda6)
- new todo (fac78020)
- Integrate analytics, gamification, and community modules (42d54caa)
- Add analytics dashboard, gamification, and community features (e640f152)
- Add performance profiler and documentation system (62597b0f)
- Add tournament tracker and theme system (1f733fc1)
- Add advanced reporting and network analysis modules (8a43acf6)
- Add session management and database optimization systems (813d152f)
- Add study mode and range analyzer features (5c87e5b0)
- Add bluff detection and hand converter systems (c0878f34)
- Modularize enhanced GUI sections (ae391dcd)
- Restore legacy poker_gui_enhanced interface (9001a99d)
- Embed manual assistant inside enhanced GUI (e309f768)
- Add internationalization support and localization UI (42773d73)
- todo (90fc8d22)
- Update progress summary (75e3448c)
- Implement coaching integration system (dcc1ad83)
- Add HUD customization designer (0aa38ed9)
- new (f57f79ff)
- log (21c4488b)
- Update master_log.txt with latest session (c2278bbb)
- Add missing auto_gto_var checkbox to fix autopilot error (ea24f44f)
- Update master_log.txt (8fceb186)
- Change quick action button text to black for better readability (bcce6e40)
- Enhance quick action button visibility - larger fonts, better contrast, improved styling (d292e12b)
- Fix indentation error in enhanced_gui.py - add missing auto_detect checkbox initialization (c56601b7)
- Update enhanced_gui.py (10a26d6b)
- saves (68ef8cfb)
- 30SEP-WORKING (f75e1917)
- push0500 (de9d6b2a)
- cmt (7b54a8e8)
- morning6 (fc682295)
- morning4 (771317c4)
- morning4 (8ef3b952)
- morning3 (c17f6a26)
- morning2 (95ededc1)
- update morning (80e310ce)
- save (248d77eb)
- Prefer packaged CLI launcher from start.py (48ece84c)
- Make enhanced GUI the default launcher (203e874e)
- Fix frontend App.tsx encoding and update master log (5cdbb0e9)
- gggg (e1c1f58d)
- Normalize frontend metadata headers (f1f352de)
- Add GUI screen scraper indicator and fix index header (b1463157)
- Merge pull request #17 from gmanldn/develop (b96e2955)
- fixes (8e570bda)
- update (e00143cb)
- changes (e40cda03)
- new30sep (d41da8a9)
- master log (e2403fd2)
- Version 28 working (7cfbe605)
- codex fix (80c0dc5a)
- tests (78fc3935)
- fixes (7299837e)
- 29sep2330 (e2d7abbd)
- new2 (dd7c1585)
- removebak (1708b7c7)
- docs (c785bd23)
- commit all (5048e664)
- git ignore (00b3da43)
- untrack2 vector (363919f7)
- untrack expermiment (0c2d424a)
- Massive new commit-Unverified (11e39d68)
- Clean up repository: untrack temporary and build files (c8455ae4)
- gg (a2ee75da)
- 23 sep GPT (e9843c37)
- Save latest changes (0fe5db06)
- Merge pull request #15 from gmanldn/main (c5068c74)
- Merge pull request #14 from gmanldn/develop (be893843)
- Clean up deleted files and prepare for merge from main (5978a2a0)
- v76 (64a37801)
- Merge branch 'main' into develop (9f133aa4)
- Add comprehensive git automation scripts and version 25 update (0ff7c83d)
- Fixed update-v24.py with safety checks to prevent mass deletions (af99d78d)
- Final commit: Add update-v24.py and update .gitignore (b62d1148)
- Merge pull request #13 from gmanldn/develop (88a5d520)
- Merge pull request #12 from gmanldn/main (fea1e5d1)
- v23 (24bd29fc)
- commmit all (5cdf3fa7)
- Merge py_lines.py fixes from develop branch (9b4ec628)
- Merge pull request #10 from gmanldn/develop (6bdb8cb7)
- Merge pull request #9 from gmanldn/develop (dcab5da2)
- Merge pull request #8 from gmanldn/develop (493abed0)

## [3.30.4] - 2025-10-07


### 🚀 Features

- Complete GTO-DEV-001 and mark all TODO tasks complete (982cfc72)
- Add comprehensive bootstrap scripts for all platforms (bde122a4)
- add GTO deviation engine and integrate with solver API (b8ea702c)

### 🐛 Bug Fixes

- Correct Suit enum case in fallback definition (v20.0.1) (d21c3633)
- **pokertool**: use autopilot panel state start_time to avoid AttributeError in _start_autopilot (8a3321ca)
- set button text color to black for improved readability on home screen (1eb7037c)

### 📚 Documentation

- update headers to v28.1.0 across all documentation (5943a1f1)
- normalise README encoding + create lightweight root README; move full guide to docs/ (01cf42fc)

### ♻️ Code Refactoring

- move remaining refactoring documentation to docs/refactoring/ (002359be)
- Fix nested package structure and corrupted files (de6abce7)
- tidy root python layout (71770e37)
- **shared**: move mistral provider data to module (8ba97495)
- **shared**: extract doubao provider metadata (58fbdd64)
- **shared**: isolate qwen provider metadata (543942fe)
- **shared**: modularize gemini provider metadata (473ccaf3)
- **shared**: extract openrouter metadata module (fd44ec14)
- **shared**: move vertex provider metadata to module (805dfad8)
- **shared**: separate bedrock provider metadata (6d2d68f1)
- **shared**: extract claude code provider metadata (70bf1c35)
- **shared**: modularize anthropic provider metadata (ee87cd1d)
- **shared**: extract API base types module (5a36d903)
- streamline screen scraping pipeline (fe9f95fc)

### 🧹 Chores

- enhance PyTorch installation robustness with version checks, documentation updates, and test (360fa337)
- improve accessibility — high contrast buttons and bold interface text (a9079d43)
- automate frontend deps and ml test guard (4074dccb)
- remove cruft and optimize opponent stats (85b49e30)

### Other Changes

- Bump version to 3.30.4 (ad010496)
- Fix syntax error: add missing # to comment on line 717 in adaptive_ui_detector.py (712f0a2d)
- Fix syntax error in adaptive_ui_detector.py - complete logger.info() statement on line 764 (dc1d0e60)
- Implement adaptive UI detection and multi-table segmenter (81ab1b25)
- new (7ce94082)
- Final enhancements: torch fallbacks, reduced debug output, definitive launcher (8a838f40)
- Enhanced documentation with accurate metrics and detailed features (49704ed4)
- Comprehensive documentation update for v29.0.0 (2611af5a)
- Major Update: Complete dependency validation and robust GUI system (f9d99543)
- Implement optimal multi-tab layout with configuration defaults (0dacd0ef)
- Fix all GUI import errors and create missing tab modules (2a4e59cc)
- Fix Python compatibility issues and dataclass slots support (9abbdbcc)
- Fix torch dependency issue: Remove torch.Tensor type annotation causing import errors (60c06d0e)
- Implement top 2 TODO tasks: SCRAPE-010 Adaptive UI Detection & SCRAPE-011 Multi-Table Segmenter (fc680f85)
- Capture blind and dealer seats in Betfair screen scraper (98941606)
- todo (ada3c261)
- Add torch/easyocr deps and create debug loop script (d0c27e48)
- Refine bootstrap to handle optional deps and default GUI (69df313a)
- Restore core module and guard CLI when Tk is missing (45d978dc)
- refactor (cfe6dc31)
- spades issue (dd361ca5)
- Oct_03_Early_new (828ff64e)
- ignore (cc4d869a)
- new (ac9fa32c)
- newoct_start (ff7b437d)
- cmt_2Oct_new (47a0a49c)
- Experimental (ebcdeed2)
- start (5a594f9c)
- start changes (e45f2356)
- saves_new (18b0e5f2)
- update to ignore (226fd0dd)
- update (1bedca9b)
- card recs (a1edaa31)
- scraper new version (f09ca603)
- scraper (394e5c5b)
- cmt (aa5eed64)
- scrape (67022060)
- late (5ff1bcc9)
- cmt (47de50ce)
- fixes (6cc9cd49)
- Merge branch 'develop' of https://github.com/gmanldn/pokertool into develop (7796a9c0)
- Merge pull request #20 from gmanldn/main (5d98f699)
- Merge pull request #19 from gmanldn/develop (d6e3a1f6)
- Fix PokerTool initialization errors (6c14b9bb)
- log (2ee19860)
- bugs (b909383f)
- gemini robust (3cf307ac)
- new gemini code (25a965c7)
- Merge pull request #18 from gmanldn/develop (86562ff2)
- Fix syntax errors reported in [master_log.txt](http://_vscodecontentref_/1) (placeholder fixes for generic errors) (7daa528c)
- Fix syntax errors reported in [master_log.txt](http://_vscodecontentref_/1) (placeholder fixes for generic errors) (8634bcca)
- gi (b9790832)
- chNGES (af1abfb6)
- Fix Suit import fallback and suit enumeration in poker_screen_scraper (3ded8fbd)
- Fix plus notation, grid initialization, and grid auto-refresh on add_range_string (d0edb46a)
- Release Version 28: Fixed test syntax errors and updated version numbers (fcbf51c4)
- Add comprehensive screen scraping refinements and performance optimizations (3e9fbda7)
- Implement desktop-independent screen scraping without Chrome dependencies (6149d161)
- Implement comprehensive master logging system with enhanced error capture (35fc125a)
- Implement SOLVER-API-001 and ENSEMBLE-001: Real-Time Solver API and Ensemble Decision System (e108a5f9)
- Implement META-001 and PREFLOP-001: Meta-Game Optimizer and Preflop Charts (0f111d7a)
- Complete TIMING-001 and STATS-001 tasks (f2427d10)
- Implement TIMING-001 and STATS-001: Timing Analyzer and Statistical Validator (a891dfa0)
- Update TODO.md: Mark MERGE-001 and QUANTUM-001 as completed (9fcb25ba)
- Complete MERGE-001 and QUANTUM-001: Advanced Range Merging and Quantum-Inspired Optimization (8b04ac34)
- Implement TIMING-001 and META-001: Timing Analyzer and Meta-Game Optimizer (d444a70a)
- Implement MERGE-001 and QUANTUM-001: Advanced Range Merging and Quantum Optimization (ee00b6bb)
- Complete BAYES-001 and RL-001: Mark tasks as completed in TODO.md (e95b96ae)
- Fix NumPy deprecation warning in RL Agent value network (65edf1b6)
- Implement BAYES-001 and RL-001: Bayesian Opponent Profiler and RL Agent (958e286b)
- Implement BAYES-001 and RL-001: Bayesian Opponent Profiler and RL Agent (6d0b979f)
- Complete MCTS-001 and ICM-001: Mark tasks as completed in TODO.md (9a091774)
- upd (4a8b8304)
- save off feature file (aa690ee3)
- Further todo updates (d07972b3)
- TODO tasks done (4407cda6)
- new todo (fac78020)
- Integrate analytics, gamification, and community modules (42d54caa)
- Add analytics dashboard, gamification, and community features (e640f152)
- Add performance profiler and documentation system (62597b0f)
- Add tournament tracker and theme system (1f733fc1)
- Add advanced reporting and network analysis modules (8a43acf6)
- Add session management and database optimization systems (813d152f)
- Add study mode and range analyzer features (5c87e5b0)
- Add bluff detection and hand converter systems (c0878f34)
- Modularize enhanced GUI sections (ae391dcd)
- Restore legacy poker_gui_enhanced interface (9001a99d)
- Embed manual assistant inside enhanced GUI (e309f768)
- Add internationalization support and localization UI (42773d73)
- todo (90fc8d22)
- Update progress summary (75e3448c)
- Implement coaching integration system (dcc1ad83)
- Add HUD customization designer (0aa38ed9)
- new (f57f79ff)
- log (21c4488b)
- Update master_log.txt with latest session (c2278bbb)
- Add missing auto_gto_var checkbox to fix autopilot error (ea24f44f)
- Update master_log.txt (8fceb186)
- Change quick action button text to black for better readability (bcce6e40)
- Enhance quick action button visibility - larger fonts, better contrast, improved styling (d292e12b)
- Fix indentation error in enhanced_gui.py - add missing auto_detect checkbox initialization (c56601b7)
- Update enhanced_gui.py (10a26d6b)
- saves (68ef8cfb)
- 30SEP-WORKING (f75e1917)
- push0500 (de9d6b2a)
- cmt (7b54a8e8)
- morning6 (fc682295)
- morning4 (771317c4)
- morning4 (8ef3b952)
- morning3 (c17f6a26)
- morning2 (95ededc1)
- update morning (80e310ce)
- save (248d77eb)
- Prefer packaged CLI launcher from start.py (48ece84c)
- Make enhanced GUI the default launcher (203e874e)
- Fix frontend App.tsx encoding and update master log (5cdbb0e9)
- gggg (e1c1f58d)
- Normalize frontend metadata headers (f1f352de)
- Add GUI screen scraper indicator and fix index header (b1463157)
- Merge pull request #17 from gmanldn/develop (b96e2955)
- fixes (8e570bda)
- update (e00143cb)
- changes (e40cda03)
- new30sep (d41da8a9)
- master log (e2403fd2)
- Version 28 working (7cfbe605)
- codex fix (80c0dc5a)
- tests (78fc3935)
- fixes (7299837e)
- 29sep2330 (e2d7abbd)
- new2 (dd7c1585)
- removebak (1708b7c7)
- docs (c785bd23)
- commit all (5048e664)
- git ignore (00b3da43)
- untrack2 vector (363919f7)
- untrack expermiment (0c2d424a)
- Massive new commit-Unverified (11e39d68)
- Clean up repository: untrack temporary and build files (c8455ae4)
- gg (a2ee75da)
- 23 sep GPT (e9843c37)
- Save latest changes (0fe5db06)
- Merge pull request #15 from gmanldn/main (c5068c74)
- Merge pull request #14 from gmanldn/develop (be893843)
- Clean up deleted files and prepare for merge from main (5978a2a0)
- v76 (64a37801)
- Merge branch 'main' into develop (9f133aa4)
- Add comprehensive git automation scripts and version 25 update (0ff7c83d)
- Fixed update-v24.py with safety checks to prevent mass deletions (af99d78d)
- Final commit: Add update-v24.py and update .gitignore (b62d1148)
- Merge pull request #13 from gmanldn/develop (88a5d520)
- Merge pull request #12 from gmanldn/main (fea1e5d1)
- v23 (24bd29fc)

## [release] - 2025-09-20


### 🚀 Features

- Complete Cloud Deployment (CLOUD-001) (27758538)

### Other Changes

- commmit all (5cdf3fa7)
- Merge py_lines.py fixes from develop branch (9b4ec628)
- Fix py_lines.py (5bf6039c)
- Merge pull request #10 from gmanldn/develop (6bdb8cb7)
- Commit all remaining changes: cache files, logs, and updated AI.md (89b11bfb)
- Fix remaining 6 bare except clauses - final VSCode linting issues resolved (815ab8e7)
- Fix VSCode linting issues: replace print statements with logging (0e65d7da)
- Add enhanced launcher and GUI improvements (8654de67)
- Complete screen scraping system optimization (f68e2b54)
- Fix failing tests (91c8f27d)
- Update master log (eff3d9ad)
- Remove interactive database initialization prompt (2c8fedc8)
- Fix GUI imports and enum references in start.py (94e73c48)
- Successful run of start.py - all core functionality working (8b08de3a)
- Fix unit tests: Resolve 14+ failing tests, improve core functionality (97877636)
- Merge pull request #9 from gmanldn/develop (dcab5da2)
- ammend (bff518bd)
- Merge pull request #8 from gmanldn/develop (493abed0)
- Merge pull request #7 from gmanldn/main (de7e2292)
- Update master_log.txt with syntax error fixes (cb771c49)
- Merge pull request #6 from gmanldn/experimental (a76f3536)
- Add all current project files and recreate project structure (9631fbc3)
- Major cleanup: Remove and recreate project files and dependencies (b8bce436)
- Remove venv directory from Git tracking and fix .gitignore (b9b83e0f)
- Merge remote-tracking branch 'origin/main' into experimental (f2ab33ee)
- ppty (8c06607d)
- Update poker tool with ONNX fixes, VectorCode integration, and venv setup (fc12ba6f)
- V41_beta (4fc8746b)
- save-dowm (bfcd4ab1)
- cmt (b4295150)
- massive2 (2558805f)
- massive (75168723)
- another big one (69576dea)
- changes (ab37394e)
- save (428af2cd)
- BIG (e8d32380)
- Version 40 (9fce4eb1)
- Merge pull request #4 from gmanldn/develop (38826ddf)
- Merge pull request #4 from gmanldn/develop (90337126)
- cmt (693bab05)
- cmt (eae19190)
- small (4441462d)
- save (f3a45ab0)
- TESTY (14b044d8)
- GUI (b8a89478)
- Remove .DS_Store from tracking (already in .gitignore) (0a02a984)
- save (dd1ba6b5)
- hhh (d4e4a521)
- Merge pull request #3 from gmanldn/develop (9a41f1df)
- Merge pull request #3 from gmanldn/develop (1295a1c9)
- save (776fcef4)
- AI file (7750c971)
- BIG_CHANGES (c6b441eb)
- cmt (e4fdda1d)
- NEW_BIG_VER (0cfbd8f6)
- Fix critical syntax errors in core.py (d07fd6be)
- big1 (f74d8ee0)
- changes (d35a7d6c)
- v22 (66d5df5a)
- Merge pull request #2 from gmanldn/develop (41ab3be5)
- Merge pull request #2 from gmanldn/develop (ccae2566)
- lots (cce1c825)
- kkk (f3f5504b)
- new (23ef1e91)
- update (3c771012)
- changes (ca17ce3b)
- fix (7b062f87)
- logger (2f12da93)
- logger (6a3c93ae)
- logger (0968f6b6)
- logger (dbb81592)
- csg (b10d4b0c)
- fixes (a1a7a968)
- upd (257414fe)
- start added (9b99ad90)
- go-change (6f52d234)
- syncheck (67e0c1a2)
- cs update (08ae31bf)
- code scan in (2ecdd1c7)
- fixes (86d8ab63)
- GG_Whoop (2aeb2845)
- Milestone (635e4f4d)
- Big chaNGES (84f08fef)
- Lots (824346df)
- Lots (66d64b57)
- big changes (4f1ba349)
- Enhanced GUI v21: Visual card selection, improved table visualization (20659b85)
- cmt (4b414c55)
- big changes (8817a2f8)
- imp4 (5fec7a0d)
- syn (f783a75e)
- cmt (01cacd64)
- improvs (3c1d546f)
- v20 (0e8851bc)
- upd (da0398ef)
- readme (158b8634)
- huge changes (7bf4c50d)
- update (1dac796e)
- go new (494fcb2a)
- 19-pp (88f8233b)
- v19-pp (04d52e6b)
- v-19-pre (26626b82)
