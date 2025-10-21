        <!-- POKERTOOL-HEADER-START
        ---
        schema: pokerheader.v1
project: pokertool
file: docs/API_DOCUMENTATION.md
version: v28.0.0
last_commit: '2025-09-23T08:41:38+01:00'
fixes:

- date: '2025-09-25'

  summary: Enhanced enterprise documentation and comprehensive unit tests added
  summary: Enhanced enterprise documentation and comprehensive unit tests added
        ---
        POKERTOOL-HEADER-END -->
# PokerTool API Documentation

## Overview

PokerTool is a comprehensive poker analysis toolkit with GUI, API, screen scraping, and database capabilities. The project is designed with modularity, security, and scalability in mind.

## Architecture

### Core Modules

#### `pokertool.core`
Core poker logic and data structures.

**Classes:**

- `Rank`: Enum for card ranks (2-14/Ace)
- `Suit`: Enum for card suits (spades, hearts, diamonds, clubs)  
- `Position`: Enum for table positions (EARLY, MIDDLE, LATE, BLINDS)
- `Card`: Immutable dataclass representing a playing card
- `HandAnalysisResult`: Analysis result with strength, advice, and details

**Functions:**

- `parse_card(s: str) -> Card`: Parse string like "As" into Card object
- `analyse_hand(hole_cards, board_cards, position, pot, to_call) -> HandAnalysisResult`: Analyze poker hand

#### `pokertool.storage`
Secure SQLite database for storing hand analysis history.

**Classes:**

- `SecureDatabase`: Thread-safe database with rate limiting and security features
  - Methods: `save_hand_analysis()`, `get_recent_hands()`, `create_session()`, `backup_database()`, `cleanup_old_data()`

**Security Features:**

- Rate limiting (100 operations/minute default)
- Input validation for hand/board formats
- Size limits (100MB default)
- Automatic backups
- Security event logging

#### `pokertool.database`
Production database module supporting PostgreSQL and SQLite.

**Classes:**

- `DatabaseType`: Enum for database types
- `DatabaseConfig`: Configuration dataclass
- `ProductionDatabase`: Main database interface with connection pooling
- `PokerDatabase`: Backward-compatible wrapper class for legacy code (wraps SecureDatabase)

**Features:**

- Automatic fallback from PostgreSQL to SQLite
- Connection pooling
- Migration utilities
- Database statistics
- Backward compatibility with legacy PokerDatabase interface

**PokerDatabase Methods:**

- `save_hand_analysis(hand, board, result, session_id)`: Save hand analysis to database
- `get_recent_hands(limit, offset)`: Retrieve recent hands with pagination
- `get_total_hands()`: Get total count of hands in database

#### `pokertool.threading`
Advanced threading and async task management.

**Classes:**

- `TaskPriority`: Enum for task priorities (LOW, NORMAL, HIGH, CRITICAL)
- `ThreadSafeCounter`: Thread-safe counter implementation
- `ThreadSafeDict`: Thread-safe dictionary with type hints
- `TaskQueue`: Priority queue for tasks
- `PokerThreadPool`: Main thread pool manager
- `AsyncManager`: Async coroutine manager

**Decorators:**

- `@threaded`: Execute function in thread pool
- `@async_threaded`: Execute async function
- `@cpu_intensive`: Execute in process pool

#### `pokertool.error_handling`
Comprehensive error handling and resilience patterns.

**Functions:**

- `sanitize_input()`: Input validation and sanitization
- `retry_on_failure()`: Decorator for automatic retries with exponential backoff
- `run_safely()`: Execute function with comprehensive error handling
- `db_guard()`: Context manager for database operations

**Classes:**

- `CircuitBreaker`: Circuit breaker pattern implementation

#### `pokertool.gui`
Tkinter-based graphical user interface.

**Classes:**

- `SecureGUI`: Main GUI application with hand analysis interface

**Features:**

- Card input validation
- Hand analysis display
- History viewing
- Database management
- Screen scraper integration

#### `pokertool.scrape`
Screen scraping for online poker tables.

**Classes:**

- `ScraperManager`: Main scraper coordination

**Functions:**

- `run_screen_scraper()`: Start scraper
- `stop_screen_scraper()`: Stop scraper
- `get_scraper_status()`: Get current status
- `register_table_callback()`: Register update callbacks

#### `pokertool.api`
RESTful API with FastAPI (optional dependencies).

**Classes:**

- `UserRole`: Enum for user roles (GUEST, USER, PREMIUM, ADMIN)
- `APIUser`: User representation
- `AuthenticationService`: JWT authentication
- `ConnectionManager`: WebSocket manager
- `PokerToolAPI`: Main API application

**Endpoints:**

- `GET /health`: Health check
- `POST /auth/token`: Login
- `POST /auth/register`: Register user
- `POST /analyze/hand`: Analyze poker hand
- `GET /scraper/status`: Scraper status
- `POST /scraper/start`: Start scraper
- `POST /scraper/stop`: Stop scraper
- `GET /hands/recent`: Get recent hands
- `GET /stats/database`: Database statistics
- `WS /ws/{user_id}`: WebSocket connection

#### `pokertool.cli`
Command-line interface entry point.

**Function:**

- `main(argv=None)`: CLI entry point

## Installation

### Basic Installation
```bash
pip install -e .
```

### With Optional Dependencies

#### Screen Scraper Support
```bash
pip install -e ".[scraper]"
```

#### API Server Support
```bash
pip install -e ".[api]"
```

#### All Features
```bash
pip install -e ".[scraper,api]"
```

## Usage Examples

### Python API

```python
from pokertool.core import parse_card, analyse_hand, Position

# Parse cards
card1 = parse_card("As")
card2 = parse_card("Kh")

# Analyze hand
result = analyse_hand(
    hole_cards=[card1, card2],
    position=Position.LATE,
    pot=100,
    to_call=20
)

print(f"Strength: {result.strength}")
print(f"Advice: {result.advice}")
```

### GUI Application

```python
from pokertool.gui import SecureGUI

gui = SecureGUI()
gui.run()
```

### API Server

```python
from pokertool.api import run_api_server

# Start server (requires FastAPI dependencies)
run_api_server(host="127.0.0.1", port=8000)
```

### Database Operations

```python
from pokertool.storage import get_secure_db

db = get_secure_db()

# Save hand analysis
db.save_hand_analysis(
    hand="AsKh",
    board="QsJdTc",
    result="Straight",
    metadata={"position": "LATE"}
)

# Get recent hands
hands = db.get_recent_hands(limit=10)
```

### Threading Examples

```python
from pokertool.threading import threaded, TaskPriority

@threaded(priority=TaskPriority.HIGH)
def analyze_multiple_hands(hands):
    # This runs in thread pool with high priority
    return [analyse_hand(h) for h in hands]
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

Create `poker_config.json`:

```json
{
  "database": {
    "type": "sqlite",
    "path": "poker_decisions.db",
    "backup_retention_days": 30
  },
  "api": {
    "rate_limit": "100/minute",
    "token_expiry_minutes": 30
  },
  "scraper": {
    "interval": 1.0,
    "sites": ["GENERIC"]
  }
}
```

## Testing

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Security tests
python -m pytest tests/test_security_features.py -v

# Comprehensive tests
python -m pytest tests/test_comprehensive_features.py -v
```

## Security Considerations

1. **Input Validation**: All user inputs are sanitized
2. **Rate Limiting**: API and database operations are rate-limited
3. **Circuit Breakers**: Prevent cascade failures
4. **Authentication**: JWT-based authentication for API
5. **Database Security**: Size limits, rate limits, secure queries
6. **Error Handling**: Comprehensive error handling with logging

## Performance

- Thread pools for concurrent operations
- Process pools for CPU-intensive tasks
- Async support for I/O operations
- Connection pooling for databases
- Priority queues for task management

## Deployment

### Development
```bash
python -m pokertool.cli
```

### Production API Server
```bash
uvicorn pokertool.api:create_app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker (Example)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e ".[api,scraper]"
CMD ["uvicorn", "pokertool.api:create_app", "--host", "0.0.0.0", "--port", "8000"]
```

## License

See LICENSE file in project root.

## Contributing

1. Fork the repository
2. Create feature branch
3. Run tests
4. Submit pull request

## Support

For issues and questions, please check the GitHub repository.
