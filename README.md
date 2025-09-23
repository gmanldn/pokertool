# PokerTool

This is the lightweight README.  
For the full guide (screenshots, long walkthroughs), see **[docs/README.md](docs/README.md)**.

---
# PokerTool - Professional Poker Analysis Toolkit

## Overview

PokerTool is a comprehensive poker analysis toolkit featuring GUI interface, RESTful API, screen scraping capabilities, and secure database storage. The project is built with modularity, security, and scalability in mind.

## Project Status

✅ **Code Review Completed** (September 18, 2025)
- All syntax errors fixed
- Import dependencies resolved  
- Code compiles successfully
- Tests passing (35 passed, 35 skipped)
- Documentation updated

## Features

### Core Functionality
- **Hand Analysis**: Advanced poker hand evaluation with position and stack considerations
- **Card Parsing**: Robust card input validation and parsing
- **Position Strategy**: Recommendations based on table position
- **Board Analysis**: Flop/turn/river texture evaluation

### Advanced Features
- **GUI Interface**: Tkinter-based desktop application
- **RESTful API**: FastAPI-powered HTTP endpoints with JWT authentication
- **WebSocket Support**: Real-time updates and notifications
- **Screen Scraping**: Monitor online poker tables (experimental)
- **Database Storage**: SQLite/PostgreSQL with automatic fallback
- **Threading**: Advanced task management with priority queues
- **Security**: Rate limiting, input sanitization, circuit breakers

## Quick Start

### Installation

#### Basic Installation (Core Features Only)
```bash
pip install -e .
```
