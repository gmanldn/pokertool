#!/usr/bin/env python3
"""
Direct GUI launcher for PokerTool that bypasses import conflicts.
"""

import sys
import os
import signal
import subprocess
from pathlib import Path

# Setup paths carefully to avoid conflicts
root_dir = Path(__file__).resolve().parent
src_dir = root_dir / 'src'
venv_dir = root_dir / '.venv'

# Add ONLY the source directory to path (not the venv to avoid conflicts)
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

def cleanup_on_error():
    """Kill all pokertool processes when an error occurs."""
    try:
        import time
        current_pid = os.getpid()

        # Unix: Kill ALL pokertool-related GUI processes
        patterns = [
            'python.*start\\.py',
            'python.*enhanced_gui',
            'python.*simple_gui',
            'python.*launch.*gui',
            'python.*run_gui',
            'pokertool.*gui'
        ]

        all_pids = set()
        for pattern in patterns:
            try:
                result = subprocess.run(
                    ['pgrep', '-f', pattern],
                    capture_output=True, text=True, timeout=3
                )
                pids = [int(pid) for pid in result.stdout.strip().split('\n')
                       if pid and pid.strip() and int(pid) != current_pid]
                all_pids.update(pids)
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                pass

        if all_pids:
            print(f"🧹 Cleaning up {len(all_pids)} process(es)...")

            # Step 1: Try SIGTERM first (graceful)
            for pid in all_pids:
                try:
                    os.kill(pid, signal.SIGTERM)
                except (ProcessLookupError, PermissionError):
                    pass

            # Step 2: Wait briefly for graceful shutdown
            time.sleep(0.5)

            # Step 3: Force kill any remaining processes with SIGKILL
            for pid in all_pids:
                try:
                    os.kill(pid, 0)  # Check if still running
                    os.kill(pid, signal.SIGKILL)  # Force kill
                except (ProcessLookupError, PermissionError):
                    pass

            print("✅ Process cleanup complete")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

print("🚀 Direct PokerTool GUI Launcher")
print("=" * 40)

# Import and launch the enhanced GUI directly
try:
    print("Importing enhanced GUI...")
    from pokertool.enhanced_gui import main as gui_main
    
    print("✅ Enhanced GUI imported successfully")
    print("🎮 Starting PokerTool Enhanced GUI...")
    
    # Launch the GUI directly
    result = gui_main()
    print(f"✅ GUI exited normally (code: {result})")
    sys.exit(result)

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Trying fallback minimal GUI...")

    # Fallback to test GUI
    try:
        import tkinter as tk
        from tkinter import ttk

        class FallbackGUI(tk.Tk):
            def __init__(self):
                super().__init__()
                self.title("PokerTool - Fallback GUI")
                self.geometry("800x600")
                self.configure(bg='#1a1f2e')

                # Main content
                main_frame = tk.Frame(self, bg='#1a1f2e')
                main_frame.pack(fill='both', expand=True, padx=20, pady=20)

                title = tk.Label(
                    main_frame,
                    text="PokerTool GUI",
                    font=('Arial', 24, 'bold'),
                    bg='#1a1f2e',
                    fg='white'
                )
                title.pack(pady=30)

                # Notebook with tabs
                notebook = ttk.Notebook(main_frame)
                notebook.pack(fill='both', expand=True)

                # Create working tabs
                for tab_name in ["Autopilot", "Manual Play", "Analysis", "Settings"]:
                    frame = tk.Frame(notebook, bg='#2a3142')

                    tk.Label(
                        frame,
                        text=f"{tab_name} Tab",
                        font=('Arial', 18, 'bold'),
                        bg='#2a3142',
                        fg='white'
                    ).pack(pady=50)

                    tk.Label(
                        frame,
                        text=f"{tab_name} functionality will be available here.",
                        font=('Arial', 12),
                        bg='#2a3142',
                        fg='#94a3b8'
                    ).pack()

                    notebook.add(frame, text=tab_name)

                print(f"✅ Created fallback GUI with {notebook.index('end')} tabs")

        app = FallbackGUI()
        print("✅ Fallback GUI created, starting main loop...")
        app.mainloop()
        print("✅ Fallback GUI closed")

    except Exception as fallback_error:
        print(f"❌ Even fallback GUI failed: {fallback_error}")
        cleanup_on_error()
        sys.exit(1)

except KeyboardInterrupt:
    print("❌ Interrupted by user")
    cleanup_on_error()
    sys.exit(130)

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    cleanup_on_error()
    sys.exit(1)
