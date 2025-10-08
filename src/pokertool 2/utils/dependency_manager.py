# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: dependency_manager.py
# version: v1.0.0
# last_commit: '2025-10-02T23:00:00+00:00'
# fixes:
# - date: '2025-10-02'
#   summary: Initial implementation - automatic dependency installation
# - date: '2025-10-02'
#   summary: Handles pip packages and system packages (Tesseract)
# - date: '2025-10-02'
#   summary: Cross-platform support (macOS, Linux, Windows)
# ---
# POKERTOOL-HEADER-END
__version__ = '1'

"""
Dependency Manager for PokerTool
=================================

Automatically installs and verifies all required dependencies on startup.
Handles both Python packages (pip) and system packages (Tesseract OCR).

Features:
- Auto-install missing Python packages
- Detect and install Tesseract OCR
- Cross-platform support
- Progress reporting
- Error recovery
"""

import sys
import subprocess
import platform
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Optional

logger = logging.getLogger(__name__)

# Required Python packages
REQUIRED_PACKAGES = [
    ('mss', 'mss>=6.0.0'),
    ('cv2', 'opencv-python>=4.5.0'),
    ('PIL', 'pillow>=8.0.0'),
    ('numpy', 'numpy>=1.20.0'),
    ('pytesseract', 'pytesseract>=0.3.0'),
]

# Optional packages (won't fail if missing)
OPTIONAL_PACKAGES = [
    ('requests', 'requests>=2.25.0'),
]


class DependencyManager:
    """Manages automatic installation and verification of dependencies."""
    
    def __init__(self, auto_install: bool = True):
        """
        Initialize dependency manager.
        
        Args:
            auto_install: If True, automatically install missing packages
        """
        self.auto_install = auto_install
        self.installed_packages = []
        self.failed_packages = []
        self.system_os = platform.system()
        
    def check_and_install_all(self) -> bool:
        """
        Check and install all required dependencies.
        
        Returns:
            True if all dependencies are satisfied, False otherwise
        """
        logger.info("🔍 Checking dependencies...")
        
        # Check Python packages
        python_ok = self._check_python_packages()
        
        # Check system packages (Tesseract)
        tesseract_ok = self._check_tesseract()
        
        if python_ok and tesseract_ok:
            logger.info("✅ All dependencies satisfied")
            return True
        else:
            logger.warning("⚠️  Some dependencies missing or failed")
            return False
    
    def _check_python_packages(self) -> bool:
        """Check and install required Python packages."""
        all_ok = True
        
        for import_name, pip_name in REQUIRED_PACKAGES:
            if not self._check_package(import_name):
                logger.info(f"📦 Package '{import_name}' not found")
                
                if self.auto_install:
                    if self._install_package(pip_name):
                        logger.info(f"✅ Installed {pip_name}")
                        self.installed_packages.append(pip_name)
                    else:
                        logger.error(f"❌ Failed to install {pip_name}")
                        self.failed_packages.append(pip_name)
                        all_ok = False
                else:
                    logger.warning(f"⚠️  Missing: {pip_name} (auto-install disabled)")
                    all_ok = False
            else:
                logger.debug(f"✓ {import_name} available")
        
        return all_ok
    
    def _check_package(self, import_name: str) -> bool:
        """Check if a Python package is available."""
        try:
            __import__(import_name)
            return True
        except ImportError:
            return False
    
    def _install_package(self, pip_name: str) -> bool:
        """Install a Python package using pip."""
        try:
            logger.info(f"⏳ Installing {pip_name}...")
            
            # Use pip to install
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--quiet', pip_name],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                return True
            else:
                logger.error(f"pip install failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Installation timeout for {pip_name}")
            return False
        except Exception as e:
            logger.error(f"Installation error: {e}")
            return False
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract OCR is installed."""
        try:
            import pytesseract
            
            # Try to get Tesseract version
            version = pytesseract.get_tesseract_version()
            logger.info(f"✓ Tesseract OCR {version} found")
            return True
            
        except ImportError:
            logger.warning("pytesseract not installed yet")
            return False
        except Exception as e:
            # Tesseract not found in system
            logger.warning(f"⚠️  Tesseract OCR not found in system")
            
            if self.auto_install:
                return self._install_tesseract()
            else:
                logger.warning("ℹ️  OCR features will be limited without Tesseract")
                return False
    
    def _install_tesseract(self) -> bool:
        """Attempt to install Tesseract OCR based on platform."""
        logger.info("⏳ Attempting to install Tesseract OCR...")
        
        if self.system_os == 'Darwin':  # macOS
            return self._install_tesseract_macos()
        elif self.system_os == 'Linux':
            return self._install_tesseract_linux()
        elif self.system_os == 'Windows':
            return self._install_tesseract_windows()
        else:
            logger.error(f"Unsupported OS: {self.system_os}")
            return False
    
    def _install_tesseract_macos(self) -> bool:
        """Install Tesseract on macOS using Homebrew."""
        try:
            # Check if Homebrew is available
            result = subprocess.run(['which', 'brew'], capture_output=True)
            if result.returncode != 0:
                logger.error("❌ Homebrew not found. Please install from https://brew.sh")
                logger.info("   Then run: brew install tesseract")
                return False
            
            # Install using Homebrew
            logger.info("📦 Installing Tesseract via Homebrew...")
            result = subprocess.run(
                ['brew', 'install', 'tesseract'],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0:
                logger.info("✅ Tesseract installed successfully")
                return True
            else:
                logger.error(f"❌ Homebrew install failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Installation timeout")
            return False
        except Exception as e:
            logger.error(f"Installation error: {e}")
            return False
    
    def _install_tesseract_linux(self) -> bool:
        """Install Tesseract on Linux using apt-get."""
        try:
            logger.info("📦 Installing Tesseract via apt-get...")
            
            # Try apt-get (Debian/Ubuntu)
            result = subprocess.run(
                ['sudo', 'apt-get', 'install', '-y', 'tesseract-ocr'],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                logger.info("✅ Tesseract installed successfully")
                return True
            else:
                logger.error(f"❌ apt-get install failed: {result.stderr}")
                logger.info("ℹ️  Try manually: sudo apt-get install tesseract-ocr")
                return False
                
        except Exception as e:
            logger.error(f"Installation error: {e}")
            logger.info("ℹ️  Try manually: sudo apt-get install tesseract-ocr")
            return False
    
    def _install_tesseract_windows(self) -> bool:
        """Provide instructions for Windows Tesseract installation."""
        logger.warning("⚠️  Automatic Tesseract installation not supported on Windows")
        logger.info("📋 Please install manually:")
        logger.info("   1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        logger.info("   2. Run the installer")
        logger.info("   3. Add to PATH: C:\\Program Files\\Tesseract-OCR")
        logger.info("   4. Restart PokerTool")
        return False
    
    def get_installation_report(self) -> Dict[str, any]:
        """Get a report of installation results."""
        return {
            'installed': self.installed_packages,
            'failed': self.failed_packages,
            'system_os': self.system_os,
            'success': len(self.failed_packages) == 0
        }
    
    def print_report(self):
        """Print installation report to console."""
        report = self.get_installation_report()
        
        print("\n" + "="*60)
        print("DEPENDENCY INSTALLATION REPORT")
        print("="*60)
        
        if report['installed']:
            print("\n✅ Installed:")
            for pkg in report['installed']:
                print(f"   - {pkg}")
        
        if report['failed']:
            print("\n❌ Failed:")
            for pkg in report['failed']:
                print(f"   - {pkg}")
            print("\n⚠️  Some features may not work correctly")
        
        if report['success']:
            print("\n🎉 All dependencies satisfied!")
        
        print("="*60 + "\n")


def ensure_dependencies(auto_install: bool = True, verbose: bool = True) -> bool:
    """
    Convenience function to check and install all dependencies.
    
    Args:
        auto_install: If True, automatically install missing packages
        verbose: If True, print detailed report
    
    Returns:
        True if all dependencies satisfied, False otherwise
    
    Example:
        >>> if ensure_dependencies():
        >>>     print("Ready to run!")
        >>> else:
        >>>     print("Some dependencies missing")
    """
    # Configure logging
    if verbose:
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s'
        )
    
    # Create manager and check dependencies
    manager = DependencyManager(auto_install=auto_install)
    success = manager.check_and_install_all()
    
    # Print report if verbose
    if verbose:
        manager.print_report()
    
    return success


if __name__ == '__main__':
    # Test dependency management
    print("🔧 PokerTool Dependency Manager")
    print("Testing dependency installation...\n")
    
    success = ensure_dependencies(auto_install=True, verbose=True)
    
    if success:
        print("✅ All systems ready!")
        sys.exit(0)
    else:
        print("❌ Some dependencies missing")
        print("   Please install manually and try again")
        sys.exit(1)
