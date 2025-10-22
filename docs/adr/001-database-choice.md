# ADR 001: Database Choice - PostgreSQL with SQLite Fallback

## Status
Accepted

## Context
PokerTool needs a database solution to store:
- Hand analysis history
- Opponent profiles and statistics
- Scraper calibration data
- User sessions and security events
- ML model training data
- Application configuration

Key requirements:
- Support for both local development and production deployment
- ACID compliance for critical data (hands, financial transactions)
- Ability to handle concurrent reads/writes
- Good performance for analytical queries
- Optional cloud deployment without major refactoring

## Decision
We will use **PostgreSQL as the primary production database** with **SQLite as a fallback** for local development and testing.

### PostgreSQL (Production)
- **Pros:**
  - Full ACID compliance
  - Excellent support for concurrent operations
  - Advanced query optimization and indexing
  - JSON/JSONB support for flexible schema
  - Battle-tested for production workloads
  - Strong ecosystem and tooling
- **Cons:**
  - Requires separate server process
  - More complex setup for local development
  - Higher resource usage

### SQLite (Development/Fallback)
- **Pros:**
  - Zero configuration
  - Perfect for local development and testing
  - Single file database - easy backups
  - Fast for small datasets
  - Built into Python standard library
- **Cons:**
  - Limited concurrent write support
  - No network access
  - Not suitable for high-traffic production

## Implementation
Database abstraction layer in `src/pokertool/database.py`:

```python
class DatabaseConfig:
    db_type: DatabaseType  # SQLITE or POSTGRESQL

class PokerDatabase:
    # Unified interface works with both backends
    def save_hand_analysis(...)
    def get_recent_hands(...)
    def get_database_stats(...)
```

Configuration via environment variables:
```bash
# PostgreSQL (production)
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@host:5432/pokertool

# SQLite (development)
DATABASE_TYPE=sqlite
DATABASE_PATH=./data/pokertool.db
```

## Consequences

### Positive
- Production-ready scalability with PostgreSQL
- Simple local development with SQLite
- Easy testing without external dependencies
- Smooth migration path from SQLite → PostgreSQL
- Database-agnostic business logic

### Negative
- Need to maintain compatibility with both databases
- Some PostgreSQL features (arrays, JSONB operators) can't be used if SQLite support is required
- Additional complexity in database abstraction layer

### Mitigation
- Use parameterized queries exclusively (prevents SQL injection, maintains compatibility)
- Test against both SQLite and PostgreSQL in CI pipeline
- Document PostgreSQL-specific features that break SQLite compatibility
- Consider removing SQLite support in future if not needed

## Alternatives Considered

### MySQL/MariaDB
- **Rejected:** Less suitable for analytical workloads, inferior JSON support compared to PostgreSQL

### MongoDB
- **Rejected:** Schema flexibility not needed, ACID compliance critical, SQL better for poker analytics

### DuckDB
- **Considered:** Excellent for analytics but newer, smaller ecosystem. Could be added later for read replicas.

## References
- Database abstraction: `src/pokertool/database.py`
- Configuration: `src/pokertool/database.py:DatabaseConfig`
- Production setup: `src/pokertool/production_database.py`
- Migration guide: `scripts/migrate_sqlite_to_postgres.py`

## Notes
- Current implementation: Lines 1-500 in database.py
- Query optimization: See ADR-004 (Caching Strategy)
- Connection pooling: Implemented in production_database.py:188-236

---

**Date:** 2025-10-22
**Author:** PokerTool Team
**Reviewed by:** Database Team
