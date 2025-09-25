#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: launch_pokertool.py
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
"""
Poker Tool Launcher
Comprehensive launcher for the enhanced poker tool with autopilot functionality.
"""

import sys
import os
import subprocess
import threading
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """Check if all dependencies are installed."""
    missing_deps = []
    
    # Python dependencies
    try:
        import tkinter
        import numpy
        import cv2
        import mss
        from PIL import Image
    except ImportError as e:
        missing_deps.append(f"Python: {e}")
    
    # Node.js dependencies
    frontend_path = Path('pokertool-frontend')
    if not (frontend_path / 'node_modules').exists():
        missing_deps.append("Node.js: Frontend dependencies not installed")
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nTo install dependencies:")
        print("  Python: pip install -r requirements.txt")
        print("  Frontend: cd pokertool-frontend && npm install")
        return False
    
    return True

def launch_frontend_server():
    """Launch the React frontend development server."""
    try:
        print("🌐 Starting React frontend server...")
        frontend_path = Path('pokertool-frontend')
        
        if not frontend_path.exists():
            print("❌ Frontend directory not found")
            return None
            
        # Start React server
        process = subprocess.Popen(
            ['npm', 'start'],
            cwd=frontend_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give it time to start
        time.sleep(5)
        
        # Open browser
        webbrowser.open('http://localhost:3000')
        print("✅ Frontend server started at http://localhost:3000")
        
        return process
        
    except Exception as e:
        print(f"❌ Frontend server error: {e}")
        return None

def launch_enhanced_gui():
    """Launch the enhanced GUI with autopilot."""
    try:
        print("🤖 Starting Enhanced Poker Tool GUI...")
        
        # Add current directory to path
        sys.path.insert(0, '.')
        
        # Import and launch the enhanced GUI
        from src.pokertool.enhanced_gui import IntegratedPokerAssistant
        
        app = IntegratedPokerAssistant()
        app.mainloop()
        
    except ImportError as e:
        print(f"❌ GUI module import error: {e}")
        print("Falling back to basic GUI...")
        
        try:
            from src.pokertool.gui import EnhancedPokerAssistant
            app = EnhancedPokerAssistant()
            app.mainloop()
        except ImportError:
            print("❌ No GUI modules available")
            
    except Exception as e:
        print(f"❌ GUI launch error: {e}")

def launch_backend_api():
    """Launch the backend API server."""
    try:
        print("🔧 Starting Backend API...")
        
        from src.pokertool.api import app as flask_app
        flask_app.run(host='0.0.0.0', port=8000, debug=False)
        
    except Exception as e:
        print(f"❌ Backend API error: {e}")

def main():
    """Main launcher function."""
    print("🎰 POKER TOOL LAUNCHER 🎰")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies before launching.")
        return 1
    
    print("✅ Dependencies check passed")
    
    # Show launch options
    print("\nLaunch Options:")
    print("1. Enhanced GUI with Autopilot (Recommended)")
    print("2. Web Interface Only")
    print("3. Both GUI and Web Interface")
    print("4. Backend API Only")
    print("5. Screen Scraper Test")
    
    try:
        choice = input("\nSelect option (1-5): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n👋 Goodbye!")
        return 0
    
    if choice == '1':
        # Launch enhanced GUI
        launch_enhanced_gui()
        
    elif choice == '2':
        # Launch web interface only
        frontend_process = launch_frontend_server()
        if frontend_process:
            try:
                frontend_process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Shutting down frontend server...")
                frontend_process.terminate()
                
    elif choice == '3':
        # Launch both GUI and web interface
        print("🚀 Starting both interfaces...")
        
        # Start frontend server in background
        frontend_process = launch_frontend_server()
        
        # Start backend API in background thread
        api_thread = threading.Thread(target=launch_backend_api, daemon=True)
        api_thread.start()
        
        # Start GUI (blocking)
        launch_enhanced_gui()
        
        # Cleanup
        if frontend_process:
            frontend_process.terminate()
            
    elif choice == '4':
        # Launch backend API only
        launch_backend_api()
        
    elif choice == '5':
        # Test screen scraper
        test_screen_scraper()
        
    else:
        print("❌ Invalid option")
        return 1
    
    return 0

def test_screen_scraper():
    """Test the screen scraper functionality."""
    try:
        print("📷 Testing Screen Scraper...")
        
        import poker_screen_scraper as pss
        
        if not pss.SCRAPER_DEPENDENCIES_AVAILABLE:
            print("❌ Screen scraper dependencies not available")
            print("Install with: pip install mss opencv-python pillow")
            return
        
        scraper = pss.create_scraper('GENERIC')
        
        # Test screenshot
        print("Taking screenshot...")
        img = scraper.capture_table()
        
        if img is not None:
            print("✅ Screenshot captured successfully")
            
            # Test analysis
            print("Analyzing table state...")
            state = scraper.analyze_table(img)
            
            print(f"✅ Analysis complete:")
            print(f"  Active players: {state.active_players}")
            print(f"  Pot size: ${state.pot_size}")
            print(f"  Stage: {state.stage}")
            
            # Test calibration
            print("Testing calibration...")
            if scraper.calibrate():
                print("✅ Calibration successful")
            else:
                print("⚠️ Calibration needs adjustment")
                
            # Save debug image
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f'debug_test_{timestamp}.png'
            scraper.save_debug_image(img, filename)
            print(f"✅ Debug image saved: {filename}")
            
        else:
            print("❌ Screenshot capture failed")
            
    except Exception as e:
        print(f"❌ Screen scraper test error: {e}")

if __name__ == '__main__':
    sys.exit(main())
