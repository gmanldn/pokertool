#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: launch_enhanced_gui_v2.py
# version: v21.0.0
# last_commit: 2025-10-12T00:00:00Z
# fixes:
#   - date: 2025-10-12
#     summary: Launcher script for enhanced GUI v2
# ---
# POKERTOOL-HEADER-END

PokerTool Enhanced GUI Launcher
================================

Simple launcher script for the enhanced poker tool GUI with integrated
screen scraping functionality.

Usage:
------
    python launch_enhanced_gui_v2.py
    
Or make executable and run directly:
    chmod +x launch_enhanced_gui_v2.py
    ./launch_enhanced_gui_v2.py

Requirements:
-------------
- Python 3.7+
- tkinter (usually included with Python)
- All dependencies from requirements.txt

Module: launch_enhanced_gui_v2
Author: PokerTool Development Team
"""

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pokertool_gui.log')
    ]
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are available."""
    missing = []
    
    # Check tkinter
    try:
        import tkinter
    except ImportError:
        missing.append('tkinter')
    
    # Check optional but recommended dependencies
    optional = []
    
    try:
        import numpy
    except ImportError:
        optional.append('numpy')
    
    try:
        import cv2
    except ImportError:
        optional.append('opencv-python')
    
    try:
        import mss
    except ImportError:
        optional.append('mss')
    
    try:
        import pytesseract
    except ImportError:
        optional.append('pytesseract')
    
    if missing:
        logger.error(f"Missing required dependencies: {', '.join(missing)}")
        logger.error("Please install: pip install " + ' '.join(missing))
        return False
    
    if optional:
        logger.warning(f"Missing optional dependencies: {', '.join(optional)}")
        logger.warning("Some features may be limited. Install with:")
        logger.warning(f"pip install {' '.join(optional)}")
    
    return True

def main():
    """Main entry point."""
    logger.info("=" * 70)
    logger.info("PokerTool Enhanced GUI v21.0.0")
    logger.info("Enterprise Edition with Integrated Screen Scraping")
    logger.info("=" * 70)
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed. Please install required packages.")
        return 1
    
    # Add src to path
    src_path = Path(__file__).parent / 'src'
    if src_path.exists():
        sys.path.insert(0, str(src_path))
    
    # Import and run GUI
    try:
        from pokertool.gui_enhanced_v2 import EnhancedPokerToolGUI
        
        logger.info("Starting GUI...")
        app = EnhancedPokerToolGUI()
        
        logger.info("GUI initialized successfully")
        logger.info("Platform: " + (app.scraper.platform if app.scraper else "Unknown"))
        
        # Run main loop
        app.mainloop()
        
        logger.info("GUI closed normally")
        return 0
        
    except ImportError as e:
        logger.error(f"Failed to import GUI module: {e}")
        logger.error("Make sure all files are in the correct location")
        return 1
    
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
