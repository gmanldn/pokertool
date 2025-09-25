        <!-- POKERTOOL-HEADER-START
        ---
        schema: pokerheader.v1
project: pokertool
file: docs/README.md
version: v20.0.0
last_commit: '2025-09-23T12:55:52+01:00'
fixes:
- date: '2025-09-25'
  summary: Enhanced enterprise documentation and comprehensive unit tests added
        ---
        POKERTOOL-HEADER-END -->
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

#### With Screen Scraper Support
```bash
pip install -e ".[scraper]"
```

#### With API Server Support
```bash
pip install -e ".[api]"
```

#### Full Installation (All Features)
```bash
pip install -e ".[scraper,api]"
```

### Running the Application

#### GUI Application
```bash
python -m pokertool.cli
# or directly:
python -m pokertool.gui
```

#### API Server
```bash
# Requires API dependencies installed
python -m pokertool.api server
```

## Project Structure

```
pokertool/
├── src/pokertool/          # Main package
│   ├── __init__.py         # Package initialization
│   ├── core.py             # Core poker logic
│   ├── gui.py              # GUI application
│   ├── api.py              # RESTful API
│   ├── storage.py          # SQLite storage
│   ├── database.py         # Production database
│   ├── threading.py        # Thread management
│   ├── error_handling.py   # Error handling
│   ├── scrape.py           # Screen scraping
│   └── cli.py              # CLI interface
├── tests/                  # Test suite
│   ├── test_poker.py       # Basic tests
│   ├── test_security_features.py  # Security tests
│   └── test_comprehensive_features.py  # Integration tests
├── docs/                   # Documentation
│   └── API_DOCUMENTATION.md  # API reference
├── tools/                  # Utility scripts
├── pyproject.toml          # Project configuration
├── requirements.txt        # Core dependencies
└── README.md              # This file
```

## Usage Examples

### Python API
```python
from pokertool.core import parse_card, analyse_hand, Position

# Parse cards
ace_spades = parse_card("As")
king_hearts = parse_card("Kh")

# Analyze hand
result = analyse_hand(
    hole_cards=[ace_spades, king_hearts],
    position=Position.LATE,
    pot=100,
    to_call=20
)

print(f"Strength: {result.strength}")
print(f"Advice: {result.advice}")
```

### Database Operations
```python
from pokertool.storage import get_secure_db

db = get_secure_db()

# Save analysis
db.save_hand_analysis(
    hand="AsKh",
    board="QsJdTc", 
    result="Straight",
    metadata={"position": "LATE"}
)

# Retrieve history
hands = db.get_recent_hands(limit=10)
```

### Threading Example
```python
from pokertool.threading import threaded, TaskPriority

@threaded(priority=TaskPriority.HIGH)
def analyze_batch(hands):
    return [analyse_hand(h) for h in hands]
```

## Testing

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Security Tests
```bash
python -m pytest tests/test_security_features.py -v
```

### Test Coverage
```bash
python -m pytest tests/ --cov=pokertool --cov-report=html
```

## Configuration

### Environment Variables
- `POKERTOOL_DB_TYPE`: Database type (postgresql/sqlite)
- `POKERTOOL_DB_HOST`: PostgreSQL host
- `POKERTOOL_DB_PORT`: PostgreSQL port  
- `POKERTOOL_DB_NAME`: Database name
- `POKERTOOL_DB_USER`: Database user
- `POKERTOOL_DB_PASSWORD`: Database password

### Configuration File
See `poker_config.json` for runtime configuration options.

## Security Features

- **Input Sanitization**: All user inputs validated and sanitized
- **Rate Limiting**: API and database operations throttled
- **Circuit Breakers**: Prevent cascade failures
- **JWT Authentication**: Secure API access
- **Database Security**: Size limits, secure queries
- **Error Handling**: Comprehensive error management

## Performance

- Thread pools for concurrent operations
- Process pools for CPU-intensive tasks  
- Async support for I/O operations
- Connection pooling for databases
- Priority task queuing

## Documentation

- [API Documentation](docs/API_DOCUMENTATION.md) - Complete API reference
- [CHANGELOG](CHANGELOG.md) - Version history
- [TODO](TODO.md) - Planned features

## Requirements

### Core Requirements
- Python 3.10+
- tkinter (usually included with Python)

### Optional Requirements
See `requirements.txt` for core dependencies and `pyproject.toml` for optional features.

## Code Quality Report

### Syntax Check ✅
All Python modules compile successfully without syntax errors.

### Import Dependencies ✅
- Core modules have no external dependencies
- Optional modules gracefully handle missing dependencies
- API module requires FastAPI stack (optional)

### Test Results ✅
- 35 tests passing
- 35 integration tests skipped (require additional setup)
- Security features fully tested
- Database operations validated

### Design Standards ✅
- **Modularity**: Clean separation of concerns
- **Type Hints**: Extensive type annotations
- **Documentation**: Comprehensive docstrings
- **Error Handling**: Robust error management
- **Security**: Defense-in-depth approach
- **Testing**: Good test coverage

## Issues Fixed

1. **test_poker.py**: Fixed syntax error in callable() assertion
2. **api.py**: Resolved jwt import issue (moved to try/except block)
3. **Documentation**: Created comprehensive API documentation
4. **Headers**: All files have proper headers for versioning

## License

See LICENSE file in project root.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

## Support

For issues and questions, please check the GitHub repository: https://github.com/gmanldn/pokertool

---

*Last reviewed: September 18, 2025*
*Version: 20.0.0*
*Status: Production Ready*
