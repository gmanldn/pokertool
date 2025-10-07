#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Dependency Manager
===========================

Comprehensive dependency validation and management system for PokerTool.
This module validates all dependencies upfront and provides detailed logging.

Module: pokertool.dependency_manager
Version: 1.0.0
Last Modified: 2025-01-07
Author: PokerTool Development Team
License: MIT
"""

import sys
import os
import platform
import subprocess
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json
import time

@dataclass
class DependencyInfo:
    """Information about a dependency."""
    name: str
    status: str  # 'available', 'missing', 'error', 'installing'
    version: Optional[str] = None
    install_command: Optional[str] = None
    error_message: Optional[str] = None
    is_critical: bool = True
    alternative_names: Optional[List[str]] = None

@dataclass
class SystemReport:
    """Complete system validation report."""
    python_dependencies: Dict[str, DependencyInfo]
    system_dependencies: Dict[str, DependencyInfo]
    optional_dependencies: Dict[str, DependencyInfo]
    platform_info: Dict[str, str]
    summary: Dict[str, int]
    recommendations: List[str]
    critical_missing: List[str]
    timestamp: str

class DependencyManager:
    """Comprehensive dependency management system."""
    
    def __init__(self, verbose: bool = True, auto_install: bool = True):
        self.verbose = verbose
        self.auto_install = auto_install
        self.report = None
        
        # Define all dependencies upfront
        self.python_dependencies = {
            # Core Python packages
            'numpy': {
                'install_command': 'numpy<2.0',
                'is_critical': True,
                'description': 'Numerical computing'
            },
            'opencv-python': {
                'install_command': 'opencv-python>=4.8.0,<4.10.0',
                'is_critical': True,
                'description': 'Computer vision',
                'import_name': 'cv2'
            },
            'opencv-contrib-python': {
                'install_command': 'opencv-contrib-python>=4.8.0,<4.10.0',
                'is_critical': False,
                'description': 'Extended OpenCV features',
                'import_name': 'cv2'
            },
            'Pillow': {
                'install_command': 'Pillow>=10.0.0',
                'is_critical': True,
                'description': 'Image processing',
                'import_name': 'PIL'
            },
            'pytesseract': {
                'install_command': 'pytesseract>=0.3.10',
                'is_critical': True,
                'description': 'OCR functionality'
            },
            'mss': {
                'install_command': 'mss>=9.0.0',
                'is_critical': True,
                'description': 'Screen capture'
            },
            'requests': {
                'install_command': 'requests>=2.32.0',
                'is_critical': True,
                'description': 'HTTP requests'
            },
            'websocket-client': {
                'install_command': 'websocket-client>=1.6.0',
                'is_critical': False,
                'description': 'WebSocket communication'
            },
            'pandas': {
                'install_command': 'pandas>=2.0.0',
                'is_critical': False,
                'description': 'Data analysis'
            },
            'scikit-learn': {
                'install_command': 'scikit-learn>=1.3.0',
                'is_critical': False,
                'description': 'Machine learning'
            },
            'joblib': {
                'install_command': 'joblib>=1.3.0',
                'is_critical': False,
                'description': 'Parallel computing'
            },
            'psutil': {
                'install_command': 'psutil>=5.9.0',
                'is_critical': False,
                'description': 'System monitoring'
            },
            'imagehash': {
                'install_command': 'imagehash',
                'is_critical': False,
                'description': 'Image hashing'
            },
            'scikit-image': {
                'install_command': 'scikit-image',
                'is_critical': False,
                'description': 'Advanced image processing'
            },
            # Optional heavy dependencies
            'torch': {
                'install_command': 'torch --extra-index-url https://download.pytorch.org/whl/cpu',
                'is_critical': False,
                'description': 'Deep learning framework',
                'skip_python_versions': [(3, 13)],  # Not available for Python 3.13 yet
            },
            'easyocr': {
                'install_command': 'easyocr',
                'is_critical': False,
                'description': 'Advanced OCR',
                'requires': ['torch']  # Requires torch
            },
            # macOS specific
            'pyobjc-framework-Quartz': {
                'install_command': 'pyobjc-framework-Quartz>=9.0',
                'is_critical': True,
                'description': 'macOS Quartz framework',
                'platforms': ['darwin'],
                'import_name': 'Quartz'
            },
        }
        
        self.system_dependencies = {
            'tkinter': {
                'description': 'GUI framework',
                'is_critical': True,
                'install_commands': {
                    'darwin': 'brew install python-tk',
                    'linux': 'apt-get install python3-tk',
                    'windows': 'Usually included with Python'
                },
                'import_name': 'tkinter'
            },
            'tesseract': {
                'description': 'OCR engine (required by pytesseract)',
                'is_critical': True,
                'install_commands': {
                    'darwin': 'brew install tesseract',
                    'linux': 'apt-get install tesseract-ocr',
                    'windows': 'Download from GitHub releases'
                },
                'test_command': 'tesseract --version'
            }
        }
    
    def log(self, message: str, level: str = 'INFO') -> None:
        """Log a message with timestamp and level."""
        if self.verbose:
            timestamp = time.strftime('%H:%M:%S')
            print(f"[{timestamp}] [{level}] [DEPS] {message}")
    
    def check_python_module(self, name: str, config: Dict[str, Any]) -> DependencyInfo:
        """Check if a Python module is available."""
        import_name = config.get('import_name', name.lower())
        
        # Check if we should skip for current Python version
        skip_versions = config.get('skip_python_versions', [])
        current_version = sys.version_info[:2]
        if current_version in skip_versions:
            return DependencyInfo(
                name=name,
                status='skipped',
                error_message=f"Not available for Python {current_version[0]}.{current_version[1]}",
                is_critical=config.get('is_critical', True),
                install_command=config.get('install_command')
            )
        
        # Check platform restrictions
        platforms = config.get('platforms', [])
        if platforms and platform.system().lower() not in platforms:
            return DependencyInfo(
                name=name,
                status='not_needed',
                error_message=f"Not needed on {platform.system()}",
                is_critical=False
            )
        
        # Check dependencies
        requires = config.get('requires', [])
        for req in requires:
            if not self._is_module_available(req):
                return DependencyInfo(
                    name=name,
                    status='dependency_missing',
                    error_message=f"Requires {req} which is not available",
                    is_critical=config.get('is_critical', True),
                    install_command=config.get('install_command')
                )
        
        try:
            # Try to import the module
            if self._is_module_available(import_name):
                # Get version if possible
                version = self._get_module_version(import_name)
                return DependencyInfo(
                    name=name,
                    status='available',
                    version=version,
                    is_critical=config.get('is_critical', True)
                )
            else:
                return DependencyInfo(
                    name=name,
                    status='missing',
                    is_critical=config.get('is_critical', True),
                    install_command=config.get('install_command')
                )
        except Exception as e:
            return DependencyInfo(
                name=name,
                status='error',
                error_message=str(e),
                is_critical=config.get('is_critical', True),
                install_command=config.get('install_command')
            )
    
    def check_system_dependency(self, name: str, config: Dict[str, Any]) -> DependencyInfo:
        """Check if a system dependency is available."""
        import_name = config.get('import_name')
        test_command = config.get('test_command')
        
        # Try import test first if specified
        if import_name:
            try:
                if self._is_module_available(import_name):
                    version = self._get_module_version(import_name)
                    return DependencyInfo(
                        name=name,
                        status='available',
                        version=version,
                        is_critical=config.get('is_critical', True)
                    )
            except Exception:
                pass
        
        # Try command test if specified
        if test_command:
            try:
                result = subprocess.run(
                    test_command.split(),
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    version = result.stdout.strip().split('\n')[0] if result.stdout else None
                    return DependencyInfo(
                        name=name,
                        status='available',
                        version=version,
                        is_critical=config.get('is_critical', True)
                    )
            except Exception:
                pass
        
        # Determine install command for current platform
        install_commands = config.get('install_commands', {})
        current_platform = platform.system().lower()
        install_cmd = install_commands.get(current_platform, 'Manual installation required')
        
        return DependencyInfo(
            name=name,
            status='missing',
            is_critical=config.get('is_critical', True),
            install_command=install_cmd
        )
    
    def _is_module_available(self, module_name: str) -> bool:
        """Check if a module can be imported."""
        return importlib.util.find_spec(module_name) is not None
    
    def _get_module_version(self, module_name: str) -> Optional[str]:
        """Get the version of an imported module."""
        try:
            module = importlib.import_module(module_name)
            # Try common version attributes
            for attr in ['__version__', 'version', 'VERSION']:
                if hasattr(module, attr):
                    version = getattr(module, attr)
                    return str(version) if version else None
        except Exception:
            pass
        return None
    
    def install_python_package(self, name: str, install_command: str) -> bool:
        """Install a Python package using pip."""
        if not self.auto_install:
            return False
        
        self.log(f"Installing {name}...")
        try:
            # Use the current Python interpreter to install
            cmd = [sys.executable, '-m', 'pip', 'install'] + install_command.split()
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.log(f"✓ Successfully installed {name}")
                return True
            else:
                self.log(f"✗ Failed to install {name}: {result.stderr}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"✗ Error installing {name}: {e}", 'ERROR')
            return False
    
    def validate_all_dependencies(self) -> SystemReport:
        """Perform comprehensive dependency validation."""
        self.log("🔍 Starting comprehensive dependency validation...")
        
        python_deps = {}
        system_deps = {}
        optional_deps = {}
        
        # Check Python dependencies
        self.log("Checking Python packages...")
        for name, config in self.python_dependencies.items():
            dep_info = self.check_python_module(name, config)
            
            if dep_info.status == 'missing' and self.auto_install and dep_info.install_command:
                self.log(f"Attempting to install missing package: {name}")
                if self.install_python_package(name, dep_info.install_command):
                    # Re-check after installation
                    dep_info = self.check_python_module(name, config)
            
            if dep_info.is_critical:
                python_deps[name] = dep_info
            else:
                optional_deps[name] = dep_info
        
        # Check system dependencies
        self.log("Checking system dependencies...")
        for name, config in self.system_dependencies.items():
            dep_info = self.check_system_dependency(name, config)
            system_deps[name] = dep_info
        
        # Generate summary
        all_deps = {**python_deps, **system_deps, **optional_deps}
        summary = {
            'total': len(all_deps),
            'available': len([d for d in all_deps.values() if d.status == 'available']),
            'missing': len([d for d in all_deps.values() if d.status == 'missing']),
            'errors': len([d for d in all_deps.values() if d.status == 'error']),
            'skipped': len([d for d in all_deps.values() if d.status in ['skipped', 'not_needed', 'dependency_missing']])
        }
        
        # Find critical missing dependencies
        critical_missing = [
            name for name, dep in all_deps.items() 
            if dep.is_critical and dep.status in ['missing', 'error']
        ]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(all_deps)
        
        # Create report
        self.report = SystemReport(
            python_dependencies=python_deps,
            system_dependencies=system_deps,
            optional_dependencies=optional_deps,
            platform_info={
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'python_version': sys.version,
                'python_executable': sys.executable
            },
            summary=summary,
            recommendations=recommendations,
            critical_missing=critical_missing,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        self._log_report()
        return self.report
    
    def _generate_recommendations(self, all_deps: Dict[str, DependencyInfo]) -> List[str]:
        """Generate actionable recommendations based on dependency status."""
        recommendations = []
        
        # Critical missing
        critical_missing = [name for name, dep in all_deps.items() 
                          if dep.is_critical and dep.status in ['missing', 'error']]
        if critical_missing:
            recommendations.append(f"CRITICAL: Install missing dependencies: {', '.join(critical_missing)}")
        
        # System-specific recommendations
        system = platform.system().lower()
        if system == 'darwin':
            if any(name == 'tkinter' and dep.status == 'missing' for name, dep in all_deps.items()):
                recommendations.append("Install tkinter: brew install python-tk")
            if any(name == 'tesseract' and dep.status == 'missing' for name, dep in all_deps.items()):
                recommendations.append("Install Tesseract OCR: brew install tesseract")
        
        # Optional improvements
        optional_missing = [name for name, dep in all_deps.items() 
                          if not dep.is_critical and dep.status == 'missing']
        if optional_missing:
            recommendations.append(f"Optional enhancements available: {', '.join(optional_missing[:3])}")
        
        return recommendations
    
    def _log_report(self) -> None:
        """Log the dependency validation report."""
        if not self.report:
            return
        
        self.log("📊 DEPENDENCY VALIDATION REPORT")
        self.log("=" * 50)
        
        # Summary
        s = self.report.summary
        self.log(f"Total dependencies: {s['total']}")
        self.log(f"✅ Available: {s['available']}")
        self.log(f"❌ Missing: {s['missing']}")
        self.log(f"⚠️  Errors: {s['errors']}")
        self.log(f"⏭️  Skipped: {s['skipped']}")
        
        # Critical missing
        if self.report.critical_missing:
            self.log(f"🚨 CRITICAL MISSING: {', '.join(self.report.critical_missing)}", 'ERROR')
        
        # Detailed status by category
        self._log_dependency_category("PYTHON PACKAGES", self.report.python_dependencies)
        self._log_dependency_category("SYSTEM DEPENDENCIES", self.report.system_dependencies)
        self._log_dependency_category("OPTIONAL FEATURES", self.report.optional_dependencies)
        
        # Recommendations
        if self.report.recommendations:
            self.log("💡 RECOMMENDATIONS:")
            for rec in self.report.recommendations:
                self.log(f"   • {rec}")
        
        # Overall status
        if not self.report.critical_missing:
            self.log("🎉 All critical dependencies are available! PokerTool is ready to run.")
        else:
            self.log("⚠️  Some critical dependencies are missing. Application may not work correctly.", 'WARN')
        
        self.log("=" * 50)
    
    def _log_dependency_category(self, title: str, deps: Dict[str, DependencyInfo]) -> None:
        """Log a category of dependencies."""
        if not deps:
            return
            
        self.log(f"📦 {title}:")
        for name, dep in deps.items():
            status_icon = {
                'available': '✅',
                'missing': '❌',
                'error': '⚠️',
                'skipped': '⏭️',
                'not_needed': '➖',
                'dependency_missing': '🔗'
            }.get(dep.status, '❓')
            
            version_info = f" v{dep.version}" if dep.version else ""
            self.log(f"   {status_icon} {name}{version_info}")
            
            if dep.error_message and self.verbose:
                self.log(f"      {dep.error_message}")
    
    def is_ready(self) -> bool:
        """Check if the system is ready (no critical dependencies missing)."""
        if not self.report:
            self.validate_all_dependencies()
        return len(self.report.critical_missing) == 0
    
    def get_missing_critical(self) -> List[str]:
        """Get list of missing critical dependencies."""
        if not self.report:
            self.validate_all_dependencies()
        return self.report.critical_missing
    
    def save_report(self, filepath: str) -> None:
        """Save the dependency report to a JSON file."""
        if not self.report:
            return
        
        # Convert to serializable format
        report_data = {
            'python_dependencies': {
                name: {
                    'name': dep.name,
                    'status': dep.status,
                    'version': dep.version,
                    'is_critical': dep.is_critical,
                    'error_message': dep.error_message,
                    'install_command': dep.install_command
                } for name, dep in self.report.python_dependencies.items()
            },
            'system_dependencies': {
                name: {
                    'name': dep.name,
                    'status': dep.status,
                    'version': dep.version,
                    'is_critical': dep.is_critical,
                    'error_message': dep.error_message,
                    'install_command': dep.install_command
                } for name, dep in self.report.system_dependencies.items()
            },
            'optional_dependencies': {
                name: {
                    'name': dep.name,
                    'status': dep.status,
                    'version': dep.version,
                    'is_critical': dep.is_critical,
                    'error_message': dep.error_message,
                    'install_command': dep.install_command
                } for name, dep in self.report.optional_dependencies.items()
            },
            'platform_info': self.report.platform_info,
            'summary': self.report.summary,
            'recommendations': self.report.recommendations,
            'critical_missing': self.report.critical_missing,
            'timestamp': self.report.timestamp
        }
        
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.log(f"📄 Report saved to {filepath}")

# Convenience functions
_global_manager: Optional[DependencyManager] = None

def get_dependency_manager(verbose: bool = True, auto_install: bool = True) -> DependencyManager:
    """Get the global dependency manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = DependencyManager(verbose=verbose, auto_install=auto_install)
    return _global_manager

def validate_system(verbose: bool = True, auto_install: bool = True) -> SystemReport:
    """Validate all system dependencies and return report."""
    manager = get_dependency_manager(verbose=verbose, auto_install=auto_install)
    return manager.validate_all_dependencies()

def is_system_ready(verbose: bool = False) -> bool:
    """Quick check if system has all critical dependencies."""
    manager = get_dependency_manager(verbose=verbose, auto_install=False)
    return manager.is_ready()

if __name__ == '__main__':
    # Run validation if called directly
    print("🔍 PokerTool Dependency Validation")
    print("=" * 40)
    
    manager = DependencyManager(verbose=True, auto_install=True)
    report = manager.validate_all_dependencies()
    
    if report.critical_missing:
        print(f"\n❌ System not ready. Missing critical dependencies: {', '.join(report.critical_missing)}")
        sys.exit(1)
    else:
        print(f"\n✅ System ready! All {report.summary['available']} critical dependencies available.")
        sys.exit(0)
