# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: start.py
# version: v28.0.0
# last_commit: '2025-01-10T17:40:00+00:00'
# fixes:
# - date: '2025-01-10'
#   summary: Complete rewrite for robust cross-platform dependency management and setup
# ---
# POKERTOOL-HEADER-END

"""
Robust cross-platform setup and launcher for PokerTool.

This script can bootstrap the entire project from nothing on Windows, macOS, and Linux.
Run with: python start.py --all (or just python start.py)
    Examples:
    python start.py --all          # Full setup and launch (default)
    python start.py --self-test    # Run comprehensive self-test (system + tests)
    python start.py --venv         # Setup virtual environment only
    python start.py --python       # Install Python dependencies only  
    python start.py --node         # Install Node dependencies only
    python start.py --tests        # Run tests only
    python start.py --validate     # Validate environment setup only
    python start.py --launch       # Launch application only
"""
from __future__ import annotations
from pathlib import Path
from typing import Sequence, Optional, Dict, Any, List
import os
import sys
import subprocess
import platform
import shutil
import venv
import argparse
import json
import subprocess
import sys
import importlib

# ✅ Dependencies for PokerTool + scraping
REQUIRED_PACKAGES = [
    "requests",
    "beautifulsoup4",
    "lxml",
    "selenium",
    "playwright",
    "pandas"
]

def install_and_import(package: str):
    """Ensure a package is installed and importable."""
    try:
        importlib.import_module(package)
    except ImportError:
        print(f"[Dependency] {package} not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    finally:
        try:
            globals()[package] = importlib.import_module(package)
        except ImportError:
            print(f"[Warning] {package} could not be imported even after install.")

def ensure_dependencies():
    """Check and install all required packages."""
    for pkg in REQUIRED_PACKAGES:
        if pkg == "playwright":
            try:
                importlib.import_module("playwright")
            except ImportError:
                print("[Dependency] Installing Playwright and browsers...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
                subprocess.check_call([sys.executable, "-m", "playwright", "install"])
        else:
            install_and_import(pkg)

# Constants
ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / 'src'
VENV_DIR = ROOT / '.venv'

# Platform detection
IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'
IS_LINUX = platform.system() == 'Linux'

class SetupError(Exception):
    """Custom exception for setup errors."""
    pass

class PlatformManager:
    """Handles platform-specific operations."""
    
    @staticmethod
    def get_python_executable() -> str:
        """Get the best Python executable for this platform."""
        candidates = []
        
        if IS_WINDOWS:
            # Windows: try py launcher first, then python, then python3
            candidates = ['py', 'python', 'python3']
        else:
            # Unix-like: try python3 first, then python
            candidates = ['python3', 'python']
        
        for cmd in candidates:
            if shutil.which(cmd):
                try:
                    result = subprocess.run([cmd, '--version'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0 and 'Python 3' in result.stdout:
                        return cmd
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    continue
        
        raise SetupError("No suitable Python 3 installation found. Please install Python 3.8 or later.")
    
    @staticmethod
    def get_venv_python() -> str:
        """Get the Python executable inside the virtual environment."""
        if IS_WINDOWS:
            return str(VENV_DIR / 'Scripts' / 'python.exe')
        else:
            return str(VENV_DIR / 'bin' / 'python')
    
    @staticmethod
    def get_venv_pip() -> str:
        """Get the pip executable inside the virtual environment."""
        if IS_WINDOWS:
            return str(VENV_DIR / 'Scripts' / 'pip.exe')
        else:
            return str(VENV_DIR / 'bin' / 'pip')
    
    @staticmethod
    def check_command_available(command: str) -> bool:
        """Check if a command is available in PATH."""
        return shutil.which(command) is not None

class DependencyManager:
    """Manages Python and Node.js dependencies."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.platform = PlatformManager()
    
    def log(self, message: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(f"[SETUP] {message}")
    
    def run_command(self, command: List[str], **kwargs) -> subprocess.CompletedProcess:
        """Run a command with proper error handling."""
        self.log(f"Running: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command, 
                check=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                **kwargs
            )
            if self.verbose and result.stdout:
                print(result.stdout)
            return result
        except subprocess.CalledProcessError as e:
            if self.verbose:
                print(e.stdout, file=sys.stdout)
                print(e.stderr, file=sys.stderr)
            error_msg = f"Command failed: {' '.join(command)}"
            if e.stderr:
                error_msg += f"\nError: {e.stderr}"
            raise SetupError(error_msg) from e
        except subprocess.TimeoutExpired as e:
            raise SetupError(f"Command timed out: {' '.join(command)}") from e
    
    def check_python_version(self) -> str:
        """Check Python version and return the executable path."""
        python_exe = self.platform.get_python_executable()
        
        try:
            result = subprocess.run([python_exe, '--version'], 
                                  capture_output=True, text=True)
            version_str = result.stdout.strip()
            self.log(f"Found {version_str}")
            
            # Parse version
            version_parts = version_str.split()[1].split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            
            if major < 3 or (major == 3 and minor < 8):
                raise SetupError(f"Python 3.8+ required, found {version_str}")
            
            return python_exe
        except Exception as e:
            raise SetupError(f"Failed to check Python version: {e}")
    
    def create_virtual_environment(self, python_exe: str) -> None:
        """Create a virtual environment."""
        if VENV_DIR.exists():
            self.log("Virtual environment already exists")
            return
        
        self.log(f"Creating virtual environment at {VENV_DIR}")
        
        try:
            # Try using built-in venv module first
            venv.create(VENV_DIR, with_pip=True)
            self.log("Virtual environment created successfully")
        except Exception as e:
            self.log(f"Built-in venv failed: {e}")
            
            # Fallback: try installing virtualenv and using it
            try:
                self.log("Installing virtualenv as fallback...")
                self.run_command([python_exe, '-m', 'pip', 'install', '--user', 'virtualenv'])
                self.run_command([python_exe, '-m', 'virtualenv', str(VENV_DIR)])
                self.log("Virtual environment created with virtualenv")
            except Exception as e2:
                raise SetupError(f"Failed to create virtual environment: {e2}") from e
    
    def upgrade_pip_in_venv(self) -> None:
        """Upgrade pip in the virtual environment."""
        venv_python = self.platform.get_venv_python()
        
        if not Path(venv_python).exists():
            raise SetupError("Virtual environment Python not found")
        
        self.log("Upgrading pip in virtual environment...")
        try:
            self.run_command([venv_python, '-m', 'pip', 'install', '--upgrade', 'pip'])
        except SetupError:
            # Try alternative upgrade method
            self.log("Trying alternative pip upgrade method...")
            self.run_command([venv_python, '-m', 'ensurepip', '--upgrade'])
            self.run_command([venv_python, '-m', 'pip', 'install', '--upgrade', 'pip'])
    
    def install_python_dependencies(self) -> None:
        """Install Python dependencies from requirements files."""
        venv_python = self.platform.get_venv_python()
        
        # Determine which requirements file to use
        requirements_lock = ROOT / 'requirements.lock'
        requirements_txt = ROOT / 'requirements.txt'
        
        requirements_file = None
        if requirements_lock.exists():
            requirements_file = requirements_lock
            self.log("Using requirements.lock for reproducible installs")
        elif requirements_txt.exists():
            requirements_file = requirements_txt
            self.log("Using requirements.txt")
        else:
            self.log("No requirements file found, skipping Python dependencies")
            return
        
        self.log(f"Installing Python dependencies from {requirements_file.name}...")
        self.run_command([
            venv_python, '-m', 'pip', 'install', '--pre', '-r', str(requirements_file)
        ])
        
        # Install additional critical dependencies that might not be in requirements
        critical_deps = [
            'opencv-python',
            'Pillow',
            'pytesseract',
            'mss',
            'numpy<2.0',  # NumPy 2.x compatibility fix
        ]
        
        self.log("Ensuring critical dependencies are installed...")
        for dep in critical_deps:
            try:
                self.run_command([venv_python, '-m', 'pip', 'install', dep])
            except SetupError:
                self.log(f"Warning: Failed to install {dep}")
    
    def check_node_available(self) -> bool:
        """Check if Node.js is available."""
        return self.platform.check_command_available('node') and self.platform.check_command_available('npm')
    
    def install_node_dependencies(self) -> None:
        """Install Node.js dependencies if package.json exists."""
        package_json = ROOT / 'package.json'
        
        if not package_json.exists():
            self.log("No package.json found, skipping Node.js dependencies")
            return
        
        if not self.check_node_available():
            self.log("Node.js/npm not found, skipping Node.js dependencies")
            self.log("Install Node.js from https://nodejs.org/ for full functionality")
            return
        
        self.log("Installing Node.js dependencies...")
        try:
            self.run_command(['npm', 'install'], cwd=ROOT)
            self.log("Node.js dependencies installed successfully")
        except SetupError as e:
            self.log(f"Warning: Node.js dependency installation failed: {e}")
    
    def validate_setup(self) -> None:
        """Validate that the setup was successful."""
        venv_python = self.platform.get_venv_python()
        
        # Check if virtual environment exists
        if not Path(venv_python).exists():
            self.log("Virtual environment not found - run with --venv first to create it")
            # Use system Python for validation
            try:
                python_exe = self.platform.get_python_executable()
                self.log(f"Using system Python for validation: {python_exe}")
                venv_python = python_exe
            except SetupError:
                self.log("No suitable Python installation found")
                return
        else:
            self.log("Using virtual environment Python for validation")
        
        # Test importing critical modules
        test_imports = [
            ('sys', 'Python standard library'),
            ('pathlib', 'Python pathlib'),
            ('numpy', 'NumPy'),
            ('cv2', 'OpenCV'),
            ('PIL', 'Pillow'),
        ]
        
        self.log("Validating Python environment...")
        for module, description in test_imports:
            try:
                result = subprocess.run([
                    venv_python, '-c', f'import {module}; print(f"{module} OK")'
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    self.log(f"✓ {description}")
                else:
                    self.log(f"⚠ {description} - {result.stderr.strip()}")
            except Exception as e:
                self.log(f"⚠ {description} - validation failed: {e}")
        
        self.log("Setup validation complete")
    
    def run_comprehensive_self_test(self) -> bool:
        """Run a comprehensive self-test including system checks."""
        self.log("=== STARTING COMPREHENSIVE SELF-TEST ===")
        
        # 1. System checks
        success = self._check_system_requirements()
        
        # 2. Environment validation
        if success:
            try:
                self.validate_setup()
                self.log("✓ Environment validation passed")
            except Exception as e:
                self.log(f"✗ Environment validation failed: {e}")
                success = False
        
        # 3. Critical dependency checks
        if success:
            success = self._check_critical_dependencies()
        
        # 4. File system checks
        if success:
            success = self._check_file_system()
        
        return success
    
    def _check_system_requirements(self) -> bool:
        """Check system-level requirements."""
        self.log("Checking system requirements...")
        
        try:
            # Check Python version
            python_exe = self.platform.get_python_executable()
            result = subprocess.run([python_exe, '--version'], 
                                  capture_output=True, text=True)
            version_str = result.stdout.strip()
            self.log(f"✓ {version_str}")
            
            # Check available memory
            try:
                import psutil
                memory = psutil.virtual_memory()
                memory_gb = memory.total / (1024**3)
                self.log(f"✓ System memory: {memory_gb:.1f} GB")
                
                if memory_gb < 4:
                    self.log("⚠ Warning: Low system memory (< 4GB)")
            except ImportError:
                self.log("⚠ psutil not available, skipping memory check")
            
            # Check disk space
            import shutil
            disk_usage = shutil.disk_usage(str(ROOT))
            free_gb = disk_usage.free / (1024**3)
            self.log(f"✓ Free disk space: {free_gb:.1f} GB")
            
            if free_gb < 1:
                self.log("⚠ Warning: Low disk space (< 1GB)")
                return False
            
            # Check platform specifics
            self.log(f"✓ Platform: {platform.system()} {platform.release()}")
            self.log(f"✓ Architecture: {platform.machine()}")
            
            return True
            
        except Exception as e:
            self.log(f"✗ System requirements check failed: {e}")
            return False
    
    def _check_critical_dependencies(self) -> bool:
        """Check critical application dependencies."""
        self.log("Checking critical dependencies...")
        
        venv_python = self.platform.get_venv_python()
        if not Path(venv_python).exists():
            venv_python = self.platform.get_python_executable()
        
        critical_modules = [
            ('numpy', 'NumPy - Mathematical operations'),
            ('cv2', 'OpenCV - Computer vision'),
            ('PIL', 'Pillow - Image processing'),
            ('tkinter', 'Tkinter - GUI framework'),
            ('sqlite3', 'SQLite - Database'),
        ]
        
    success = True
    for module, description in critical_modules:
        try:
            result = subprocess.run([
                venv_python, '-c', f'import {module}; print("OK")'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.log(f"✓ {description}")
            else:
                self.log(f"✗ {description} - FAILED")
                success = False
        except Exception as e:
            self.log(f"✗ {description} - ERROR: {e}")
            success = False
        
    return success
    
    def _check_file_system(self) -> bool:
        """Check file system structure and permissions."""
        self.log("Checking file system...")
        
        critical_paths = [
            (SRC_DIR, "Source directory"),
            (ROOT / 'tests', "Tests directory"),
            (ROOT / 'requirements.txt', "Requirements file"),
        ]
        
        success = True
        for path, description in critical_paths:
            if path.exists():
                if path.is_file() and os.access(path, os.R_OK):
                    self.log(f"✓ {description} readable")
                elif path.is_dir() and os.access(path, os.R_OK | os.X_OK):
                    self.log(f"✓ {description} accessible")
                else:
                    self.log(f"✗ {description} - permission denied")
                    success = False
            else:
                self.log(f"⚠ {description} - not found")
                if 'tests' not in str(path):  # Tests dir is optional
                    success = False
        
        # Check write permissions in project root
        try:
            test_file = ROOT / '.write_test'
            test_file.write_text('test')
            test_file.unlink()
            self.log("✓ Project directory writable")
        except Exception as e:
            self.log(f"✗ Project directory not writable: {e}")
            success = False
        
        return success

class PokerToolLauncher:
    """Handles launching the PokerTool application."""
    
    def __init__(self, dependency_manager: DependencyManager):
        self.dependency_manager = dependency_manager
        self.platform = PlatformManager()
    
    def setup_python_path(self) -> Dict[str, str]:
        """Set up the Python path for running the application."""
        env = os.environ.copy()
        
        python_paths = [str(ROOT), str(SRC_DIR)]
        existing_path = env.get('PYTHONPATH', '')
        
        if existing_path:
            python_paths.append(existing_path)
        
        env['PYTHONPATH'] = os.pathsep.join(python_paths)
        return env
    
    def run_tests(self) -> int:
        """Run the test suite."""
        venv_python = self.platform.get_venv_python()
        env = self.setup_python_path()
        
        test_file = ROOT / 'run_tests.py'
        if not test_file.exists():
            self.dependency_manager.log("No test file found, skipping tests")
            return 0
        
        self.dependency_manager.log("Running tests...")
        try:
            result = subprocess.run([venv_python, str(test_file)], 
                                  cwd=ROOT, env=env)
            return result.returncode
        except Exception as e:
            self.dependency_manager.log(f"Test execution failed: {e}")
            return 1
    
    def run_full_self_test(self) -> int:
        """Run a complete self-test including system checks, environment validation, and test suite."""
        self.dependency_manager.log("=== POKERTOOL COMPREHENSIVE SELF-TEST ===")
        
        # 1. Run comprehensive system and environment checks
        if not self.dependency_manager.run_comprehensive_self_test():
            self.dependency_manager.log("\n✗ Comprehensive self-test FAILED")
            return 1
        
        self.dependency_manager.log("✓ System and environment checks PASSED")
        
        # 2. Run the full test suite
        self.dependency_manager.log("=== RUNNING TEST SUITE ===")
        test_result = self.run_tests()
        
        if test_result != 0:
            self.dependency_manager.log("✗ Test suite FAILED")
            return test_result
        
        self.dependency_manager.log("✓ Test suite PASSED")
        
        # 3. Optional: Quick application smoke test
        self.dependency_manager.log("=== BASIC FUNCTIONALITY CHECK ===")
        if self._run_smoke_test():
            self.dependency_manager.log("✓ Basic functionality check PASSED")
        else:
            self.dependency_manager.log("⚠ Basic functionality check had issues (not critical)")
        
        self.dependency_manager.log("=== SELF-TEST COMPLETED SUCCESSFULLY ===")
        return 0
    
    def _run_smoke_test(self) -> bool:
        """Run a basic smoke test to verify core functionality."""
        try:
            venv_python = self.platform.get_venv_python()
            env = self.setup_python_path()
            
            # Test basic module imports
            smoke_test_code = '''

            result = subprocess.run([
                venv_python, '-c', smoke_test_code
            ], capture_output=True, text=True, cwd=ROOT, env=env, timeout=30)
            
            if result.returncode == 0:
                self.dependency_manager.log("✓ Basic module structure accessible")
                return True
            else:
                self.dependency_manager.log(f"⚠ Smoke test issues: {result.stderr}")
                return False'''
                
        except Exception as e:
            self.dependency_manager.log(f"⚠ Smoke test error: {e}")
            return False
    
    def launch_application(self, args: List[str] = None) -> int:
        """Launch the main PokerTool application."""
        if args is None:
            args = []
        
        venv_python = self.platform.get_venv_python()
        env = self.setup_python_path()
        
        # Try different launch methods in order of preference
        launch_methods = [
            # Method 1: Use -m pokertool
            [venv_python, '-m', 'pokertool'] + args,
            # Method 2: Direct CLI script
            [venv_python, str(SRC_DIR / 'pokertool' / 'cli.py')] + args,
            # Method 3: Legacy scripts
            [venv_python, str(ROOT / 'tools' / 'poker_go.py')] + args,
            [venv_python, str(ROOT / 'launch_pokertool.py')] + args,
        ]
        
        for method in launch_methods:
            # Check if the target file exists (skip -m methods)
            if len(method) > 2 and not method[0].endswith('python') and not Path(method[1]).exists():
                continue
            
            self.dependency_manager.log(f"Trying launch method: {' '.join(method[:2])}")
            try:
                result = subprocess.run(method, cwd=ROOT, env=env)
                return result.returncode
            except Exception as e:
                self.dependency_manager.log(f"Launch method failed: {e}")
                continue
        
        self.dependency_manager.log("All launch methods failed")
        return 1

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="PokerTool Setup and Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
"""
    )
    
    parser.add_argument('--venv', action='store_true', 
                       help='Setup virtual environment')
    parser.add_argument('--python', action='store_true',
                       help='Install Python dependencies') 
    parser.add_argument('--node', action='store_true',
                       help='Install Node.js dependencies')
    parser.add_argument('--tests', action='store_true',
                       help='Run tests')
    parser.add_argument('--launch', action='store_true',
                       help='Launch application')
    parser.add_argument('--all', action='store_true',
                       help='Do everything (setup + launch)')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress output')
    parser.add_argument('--validate', action='store_true',
                       help='Validate setup only')
    parser.add_argument('--self-test', action='store_true',
                       help='Run comprehensive self-test (system checks + full test suite)')
    
    args, unknown_args = parser.parse_known_args()
    
    # Default to --all if no specific action is specified
    if not any([args.venv, args.python, args.node, args.tests, args.launch, args.all, args.validate, args.self_test]):
        args.all = True
    
    try:
        dependency_manager = DependencyManager(verbose=not args.quiet)
        launcher = PokerToolLauncher(dependency_manager)
        
        # Platform info
        dependency_manager.log(f"Platform: {platform.system()} {platform.release()}")
        dependency_manager.log(f"Architecture: {platform.machine()}")
        dependency_manager.log(f"Python: {sys.version}")
        
        return_code = 0
        
        # Check if we're already in the virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )
        
        # Virtual environment setup
        if args.all or args.venv:
            if not in_venv:
                python_exe = dependency_manager.check_python_version()
                dependency_manager.create_virtual_environment(python_exe)
                dependency_manager.upgrade_pip_in_venv()
                
                # Re-invoke script in virtual environment if we're not already in one
                venv_python = PlatformManager.get_venv_python()
                if Path(venv_python).exists():
                    dependency_manager.log("Re-invoking script in virtual environment...")
                    # Remove --venv from args to avoid infinite recursion
                    new_args = [arg for arg in sys.argv[1:] if arg != '--venv']
                    if not new_args or (len(new_args) == 1 and new_args[0] == '--all'):
                        new_args = ['--python', '--node', '--launch']
                    
                    result = subprocess.run([venv_python, sys.argv[0]] + new_args)
                    return result.returncode
            else:
                dependency_manager.log("Already in virtual environment")
        
        # Python dependencies
        if args.all or args.python:
            dependency_manager.install_python_dependencies()
        
        # Node dependencies  
        if args.all or args.node:
            dependency_manager.install_node_dependencies()
        
        # Validation
        if args.all or args.validate:
            dependency_manager.validate_setup()
        
        # Self-test (comprehensive)
        if args.self_test:
            self_test_result = launcher.run_full_self_test()
            if self_test_result != 0:
                dependency_manager.log(f"Self-test failed with code {self_test_result}")
                return_code = self_test_result
            else:
                dependency_manager.log("✓ Comprehensive self-test completed successfully!")
            return return_code  # Exit after self-test, don't proceed to other actions
        
        # Tests
        if args.tests:
            test_result = launcher.run_tests()
            if test_result != 0:
                dependency_manager.log(f"Tests failed with code {test_result}")
                return_code = test_result
        
        # Launch application
        if args.all or args.launch:
            if return_code == 0:  # Only launch if previous steps succeeded
                dependency_manager.log("Launching PokerTool...")
                return_code = launcher.launch_application(unknown_args)
        
        if return_code == 0:
            dependency_manager.log("✓ Setup and launch completed successfully!")
        
        return return_code
        
    except SetupError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[INFO] Setup interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
