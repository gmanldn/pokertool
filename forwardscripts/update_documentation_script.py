#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: update_documentation_script.py
# version: v28.0.0
# last_commit: '2025-09-23T15:20:12.142288+00:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
# -*- coding: utf-8 -*-

"""
Automated Documentation Update Script for PokerTool
====================================================

This script automatically updates all Python files in the PokerTool repository
with comprehensive enterprise-grade documentation headers.

Usage:
    python update_documentation.py /path/to/pokertool/repo
"""

import os
import sys
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

def update_file_with_header(file_path: Path, header: str) -> bool:
    """
    Update a Python file with a new documentation header.
    
    Args:
        file_path: Path to the Python file
        header: New header content
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read existing content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find where the actual code starts (after imports and current docstring)
        # Look for the first class or function definition, or first non-import statement
        code_pattern = re.compile(
            r'^(class |def |[^#\s].*=|if __name__|@)',
            re.MULTILINE
        )
        
        # Remove existing header/docstring if present
        # Match everything up to 'from __future__' or first import
        import_match = re.search(
            r'^(from __future__ import|import |from \w+ import)',
            content,
            re.MULTILINE
        )
        
        if import_match:
            # Keep everything from first import onward
            code_content = content[import_match.start():]
        else:
            # No imports found, look for first code
            code_match = code_pattern.search(content)
            if code_match:
                code_content = content[code_match.start():]
            else:
                code_content = content
        
        # Combine new header with existing code
        new_content = header + '\n' + code_content
        
        # Create backup
        backup_path = file_path.with_suffix('.py.bak')
        shutil.copy2(file_path, backup_path)
        
        # Write updated content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✓ Updated: {file_path}")
        return True
        
    except Exception as e:
        print(f"✗ Error updating {file_path}: {e}")
        return False


def generate_specific_header(module_name: str) -> str:
    """Generate module-specific header based on module name."""
    
    # Module-specific documentation
    headers = {
        'core.py': '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Core Module
=====================

This module provides the foundational data structures and logic for poker hand analysis,
including card representation, position tracking, and basic hand evaluation algorithms.

Module: pokertool.core
Version: 20.0.0
Last Modified: {date}
Author: PokerTool Development Team
License: MIT

Dependencies:
    - Python 3.10+
    - Standard library only (enum, dataclasses, typing)

Classes:
    - Rank: Enumeration of all poker card ranks
    - Suit: Enumeration of all poker card suits  
    - Position: Enumeration of poker table positions
    - Card: Immutable dataclass representing a playing card
    - HandAnalysisResult: Dataclass containing hand analysis results

Functions:
    - parse_card: Parse string representation into Card object
    - analyse_hand: Analyze poker hand strength and provide strategic advice

Change Log:
    - v28.0.0 ({date}): Enhanced documentation, added type hints
    - v19.0.0 (2025-09-18): Fixed syntax errors
    - v18.0.0 (2025-09-15): Initial production release
"""

__version__ = '20.0.0'
__author__ = 'PokerTool Development Team'
__copyright__ = 'Copyright (c) 2025 PokerTool'
__license__ = 'MIT'
__maintainer__ = 'George Ridout'
__status__ = 'Production'
''',

        'api.py': '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool RESTful API Module
=============================

This module provides a comprehensive RESTful API for external integration
with the PokerTool application. It includes endpoints for hand analysis,
database operations, real-time updates via WebSocket, and secure authentication.

Module: pokertool.api
Version: 20.0.0
Last Modified: {date}
Author: PokerTool Development Team
License: MIT

Dependencies:
    - FastAPI >= 0.104.0: Web framework for building APIs
    - Uvicorn >= 0.24.0: ASGI server implementation
    - PyJWT >= 2.8.0: JWT token handling
    - Redis >= 5.0.0: Caching and session management
    - SlowAPI >= 0.1.9: Rate limiting middleware
    - Pydantic >= 2.5.0: Data validation
    - BCrypt: Password hashing

API Endpoints:
    - POST /analyze: Analyze poker hand
    - GET /health: Health check endpoint
    - POST /auth/login: User authentication
    - POST /auth/refresh: Token refresh
    - WS /ws: WebSocket for real-time updates

Security Features:
    - JWT-based authentication
    - Rate limiting per IP/user
    - Input validation and sanitization
    - CORS configuration
    - Circuit breaker pattern

Change Log:
    - v28.0.0 ({date}): Enhanced documentation, improved security
    - v19.0.0 (2025-09-18): Fixed JWT import issue
    - v18.0.0 (2025-09-15): Initial API implementation
"""

__version__ = '20.0.0'
__author__ = 'PokerTool Development Team'
__copyright__ = 'Copyright (c) 2025 PokerTool'
__license__ = 'MIT'
__maintainer__ = 'George Ridout'
__status__ = 'Production'
''',

        'database.py': '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Production Database Module
=====================================

Enterprise-grade database abstraction layer supporting both PostgreSQL
for production and SQLite for development. Implements connection pooling,
automatic failover, and comprehensive transaction management.

Module: pokertool.database
Version: 20.0.0
Last Modified: {date}
Author: PokerTool Development Team
License: MIT

Dependencies:
    - psycopg2 >= 2.9.0: PostgreSQL adapter (optional)
    - psycopg2-pool: Connection pooling
    - sqlite3: Built-in SQLite support

Database Features:
    - Dual database support (PostgreSQL/SQLite)
    - Connection pooling for performance
    - Automatic retry with exponential backoff
    - Transaction management with rollback
    - Query optimization and caching
    - Migration support
    - Audit logging
    - Backup and restore

Configuration:
    Environment variables:
    - POKERTOOL_DB_TYPE: 'postgresql' or 'sqlite'
    - POKERTOOL_DB_HOST: PostgreSQL host
    - POKERTOOL_DB_PORT: PostgreSQL port
    - POKERTOOL_DB_NAME: Database name