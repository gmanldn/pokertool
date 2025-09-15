#!/usr/bin/env python3
from __future__ import annotations

import sys
import os
import atexit
from pathlib import Path

# Add your project root to path if needed
sys.path.insert(0, str(Path(__file__).parent))

from logger import logger, log_exceptions, setup_global_exception_handler

def initialize_logging():
    """Initialize the logging system."""
    setup_global_exception_handler()
    logger.info(
        "APPLICATION STARTUP",
        argv=sys.argv,
        cwd=os.getcwd(),
        python_path=sys.path,
        environment_vars={k: v for k, v in os.environ.items() 
                         if 'TOKEN' not in k and 'KEY' not in k}
    )

def cleanup():
    """Cleanup function called on exit."""
    logger.info("Performing cleanup")

@log_exceptions
def main():
    """Main application entry point."""
    initialize_logging()
    
    try:
        logger.info("Starting poker tool application")
        test_value = {"cards": ["AS", "KH"], "position": "BTN"}
        logger.debug("Test debug message", test_data=test_value)
        
    except Exception as e:
        logger.critical("Application failed to start", exception=e)
        return 1
    
    logger.info("Application shutdown normally")
    return 0

if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main())