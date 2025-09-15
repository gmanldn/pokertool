#!/usr/bin/env python3
"""
Poker Assistant Setup Script
Fixes all common issues and launches the application
"""

import os
import sys
import subprocess
import traceback
from pathlib import Path

def check_python_version():
    """Check if Python version is adequate."""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required.")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_dependencies():
    """Install required packages."""
    print("\n🔧 Checking dependencies...")
    
    # Check tkinter (usually built-in)
    try:
        import tkinter
        print("✅ tkinter is available")
    except ImportError:
        print("❌ tkinter is not available. Please install python3-tkinter")
        print("On Ubuntu/Debian: sudo apt-get install python3-tkinter")
        print("On macOS: tkinter should be included with Python")
        return False
    
    return True

def check_files():
    """Check if all required files exist."""
    print("\n📁 Checking files...")
    
    required_files = [
        'poker_modules.py',
        'poker_init.py',
        'poker_gui.py',
        'poker_main.py'
    ]
    
    missing_files = []
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        print("Please ensure all poker files are in the same directory.")
        return False
    
    return True

def test_imports():
    """Test if modules can be imported."""
    print("\n🧪 Testing imports...")
    
    # Add current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    try:
        from poker_modules import Card, Suit, Position, analyse_hand
        print("✅ poker_modules imports successfully")
    except ImportError as e:
        print(f"⚠️  poker_modules import warning: {e}")
        print("Application will run with limited functionality")
    
    try:
        from poker_init import initialise_db_if_needed
        print("✅ poker_init imports successfully")
    except ImportError as e:
        print(f"⚠️  poker_init import warning: {e}")
    
    try:
        from poker_gui import PokerAssistantGUI
        print("✅ poker_gui imports successfully")
        return True
    except ImportError as e:
        print(f"❌ poker_gui import failed: {e}")
        return False

def create_config():
    """Create configuration file if needed."""
    config_file = Path("poker_config.json")
    if not config_file.exists():
        print("\n📝 Creating configuration file...")
        import json
        
        config = {
            "version": "1.0",
            "database": {
                "enabled": True,
                "file": "poker_decisions.db"
            },
            "gui": {
                "theme": "dark",
                "window_size": "1000x700"
            },
            "analysis": {
                "auto_save": True,
                "show_statistics": True
            }
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print("✅ Configuration file created")
        except Exception as e:
            print(f"⚠️  Could not create config file: {e}")

def launch_application():
    """Launch the poker assistant."""
    print("\n🚀 Launching Poker Assistant...")
    
    try:
        # Change to script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        # Add to Python path
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        
        # Import and launch
        from poker_gui import PokerAssistantGUI
        
        print("✅ Starting GUI...")
        app = PokerAssistantGUI()
        app.mainloop()
        
    except KeyboardInterrupt:
        print("\n⚠️  Application interrupted by user")
    except Exception as e:
        print(f"\n❌ Failed to launch application: {e}")
        traceback.print_exc()
        return False
    
    return True

def main():
    """Main setup and launch function."""
    print("=" * 60)
    print("       ♠♥ POKER ASSISTANT SETUP & LAUNCH ♦♣")
    print("=" * 60)
    
    # Step 1: Check Python version
    if not check_python_version():
        return False
    
    # Step 2: Install dependencies
    if not install_dependencies():
        return False
    
    # Step 3: Check files
    if not check_files():
        return False
    
    # Step 4: Test imports
    if not test_imports():
        print("\n⚠️  Some imports failed, but attempting to continue...")
    
    # Step 5: Create config
    create_config()
    
    # Step 6: Launch application
    print("\n" + "=" * 60)
    success = launch_application()
    
    if success:
        print("\n✅ Application closed successfully")
    else:
        print("\n❌ Application encountered errors")
        print("\nTroubleshooting:")
        print("1. Ensure all .py files are in the same directory")
        print("2. Check that Python 3.7+ is installed")
        print("3. Verify tkinter is available")
        print("4. Try running: python3 poker_main.py")
    
    print("=" * 60)
    return success

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
