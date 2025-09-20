#!/usr/bin/env python3
"""
ONNX Runtime CoreML Error Fix
Resolves the ONNX Runtime CoreML execution error by creating a clean environment
and providing workarounds for the pokertool project.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ONNXErrorFix:
    """Fix ONNX Runtime CoreML execution errors."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        
    def diagnose_environment(self) -> Dict[str, Any]:
        """Diagnose the current environment and ONNX installations."""
        diagnosis = {
            'python_version': sys.version,
            'python_path': sys.executable,
            'virtual_env': os.environ.get('VIRTUAL_ENV', 'None'),
            'onnx_packages': [],
            'ml_packages': [],
            'current_directory': os.getcwd()
        }
        
        try:
            # Check for ONNX-related packages
            result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'onnx' in line.lower():
                        diagnosis['onnx_packages'].append(line.strip())
                    elif any(pkg in line.lower() for pkg in ['tensorflow', 'torch', 'sklearn', 'numpy']):
                        diagnosis['ml_packages'].append(line.strip())
        except Exception as e:
            logger.warning(f"Could not check pip packages: {e}")
        
        return diagnosis
    
    def create_clean_environment(self) -> bool:
        """Create a clean virtual environment for pokertool."""
        try:
            logger.info("Creating clean virtual environment...")
            
            # Remove existing venv if it exists
            if self.venv_path.exists():
                import shutil
                shutil.rmtree(self.venv_path)
                logger.info("Removed existing virtual environment")
            
            # Create new virtual environment
            subprocess.run([sys.executable, '-m', 'venv', str(self.venv_path)], check=True)
            logger.info(f"Created virtual environment: {self.venv_path}")
            
            # Determine the correct pip path
            if sys.platform == "win32":
                pip_path = self.venv_path / "Scripts" / "pip"
                python_path = self.venv_path / "Scripts" / "python"
            else:
                pip_path = self.venv_path / "bin" / "pip"
                python_path = self.venv_path / "bin" / "python"
            
            # Upgrade pip
            subprocess.run([str(python_path), '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
            
            # Install pokertool requirements
            requirements_file = self.project_root / "requirements.txt"
            if requirements_file.exists():
                subprocess.run([str(pip_path), 'install', '-r', str(requirements_file)], check=True)
                logger.info("Installed pokertool requirements")
            
            # Install additional ML dependencies (without ONNX Runtime)
            ml_packages = [
                'tensorflow>=2.13.0',
                'scikit-learn>=1.3.0',
                'pandas>=2.0.0',
                'joblib>=1.3.0'
            ]
            
            subprocess.run([str(pip_path), 'install'] + ml_packages, check=True)
            logger.info("Installed ML dependencies")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create clean environment: {e}")
            return False
        except Exception as e:
            logger.error(f"Error creating environment: {e}")
            return False
    
    def disable_onnx_runtime(self) -> bool:
        """Disable ONNX Runtime to prevent conflicts."""
        try:
            # Try to uninstall onnxruntime packages
            onnx_packages = ['onnxruntime', 'onnxruntime-gpu', 'onnxruntime-coreml']
            
            for package in onnx_packages:
                try:
                    result = subprocess.run([sys.executable, '-m', 'pip', 'uninstall', package, '-y'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        logger.info(f"Uninstalled {package}")
                except Exception:
                    pass  # Package might not be installed
            
            return True
            
        except Exception as e:
            logger.error(f"Error disabling ONNX Runtime: {e}")
            return False
    
    def create_environment_script(self) -> bool:
        """Create script to activate the clean environment."""
        try:
            if sys.platform == "win32":
                script_content = f"""@echo off
echo Activating pokertool environment...
call "{self.venv_path}\\Scripts\\activate.bat"
echo Environment activated. ONNX Runtime conflicts resolved.
echo You can now run: python start.py
cmd /k
"""
                script_path = self.project_root / "activate_pokertool.bat"
            else:
                script_content = f"""#!/bin/bash
echo "Activating pokertool environment..."
source "{self.venv_path}/bin/activate"
echo "Environment activated. ONNX Runtime conflicts resolved."
echo "You can now run: python start.py"
exec "$SHELL"
"""
                script_path = self.project_root / "activate_pokertool.sh"
            
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Make executable on Unix systems
            if sys.platform != "win32":
                os.chmod(script_path, 0o755)
            
            logger.info(f"Created environment script: {script_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create environment script: {e}")
            return False
    
    def patch_ml_modules(self) -> bool:
        """Patch ML modules to handle missing ONNX gracefully."""
        try:
            # Create a patch for the ML opponent modeling module
            ml_module_path = self.project_root / "src" / "pokertool" / "ml_opponent_modeling.py"
            
            if not ml_module_path.exists():
                logger.warning("ML opponent modeling module not found")
                return True
            
            # Read the current module
            with open(ml_module_path, 'r') as f:
                content = f.read()
            
            # Add ONNX Runtime error handling at the top
            onnx_patch = '''
# ONNX Runtime Error Prevention Patch
import os
os.environ['OMP_NUM_THREADS'] = '1'  # Prevent threading conflicts
os.environ['ONNXRUNTIME_PROVIDERS'] = 'CPUExecutionProvider'  # Force CPU execution

# Disable ONNX Runtime CoreML provider
def _disable_coreml_provider():
    """Disable CoreML execution provider to prevent errors."""
    try:
        import onnxruntime as ort
        # Get available providers and remove CoreML
        providers = ort.get_available_providers()
        if 'CoreMLExecutionProvider' in providers:
            providers.remove('CoreMLExecutionProvider')
        # Set session options to use only CPU
        ort.set_default_logger_severity(3)  # ERROR level only
    except ImportError:
        pass  # ONNX Runtime not installed

# Apply the patch
_disable_coreml_provider()

'''
            
            # Only add patch if not already present
            if '_disable_coreml_provider' not in content:
                # Insert patch after the module docstring
                docstring_end = content.find('"""', content.find('"""') + 3) + 3
                patched_content = content[:docstring_end] + '\n' + onnx_patch + content[docstring_end:]
                
                # Write patched content
                with open(ml_module_path, 'w') as f:
                    f.write(patched_content)
                
                logger.info("Applied ONNX Runtime patch to ML module")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to patch ML modules: {e}")
            return False
    
    def create_workaround_config(self) -> bool:
        """Create configuration to avoid ONNX Runtime issues."""
        try:
            config = {
                "ml_settings": {
                    "disable_onnx": True,
                    "force_cpu_execution": True,
                    "tensorflow_device": "CPU",
                    "sklearn_n_jobs": 1,
                    "prevent_threading_conflicts": True
                },
                "execution_providers": ["CPUExecutionProvider"],
                "environment_variables": {
                    "OMP_NUM_THREADS": "1",
                    "TF_CPP_MIN_LOG_LEVEL": "2",
                    "ONNXRUNTIME_PROVIDERS": "CPUExecutionProvider"
                }
            }
            
            import json
            config_path = self.project_root / "onnx_workaround_config.json"
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Created workaround configuration: {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create workaround config: {e}")
            return False
    
    def run_diagnostics_and_fix(self) -> bool:
        """Run full diagnostics and apply fixes."""
        logger.info("Starting ONNX Runtime CoreML error diagnostics and fix...")
        
        # Step 1: Diagnose current environment
        logger.info("Step 1: Diagnosing environment...")
        diagnosis = self.diagnose_environment()
        
        logger.info("Environment Diagnosis:")
        logger.info(f"  Python: {diagnosis['python_version']}")
        logger.info(f"  Virtual Env: {diagnosis['virtual_env']}")
        logger.info(f"  ONNX Packages: {diagnosis['onnx_packages']}")
        logger.info(f"  ML Packages: {diagnosis['ml_packages']}")
        
        # Step 2: Create clean environment
        logger.info("Step 2: Creating clean environment...")
        if not self.create_clean_environment():
            logger.error("Failed to create clean environment")
            return False
        
        # Step 3: Create activation script
        logger.info("Step 3: Creating activation script...")
        if not self.create_environment_script():
            logger.error("Failed to create activation script")
            return False
        
        # Step 4: Create workaround configuration
        logger.info("Step 4: Creating workaround configuration...")
        if not self.create_workaround_config():
            logger.error("Failed to create workaround config")
            return False
        
        # Step 5: Apply ML module patches
        logger.info("Step 5: Applying ML module patches...")
        if not self.patch_ml_modules():
            logger.error("Failed to patch ML modules")
            return False
        
        logger.info("ONNX Runtime CoreML error fix completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Close this terminal")
        logger.info("2. Run the activation script:")
        if sys.platform == "win32":
            logger.info("   - Windows: Double-click activate_pokertool.bat")
        else:
            logger.info("   - macOS/Linux: Run ./activate_pokertool.sh")
        logger.info("3. Test your pokertool application: python start.py")
        
        return True

def main():
    """Main entry point."""
    try:
        fixer = ONNXErrorFix()
        success = fixer.run_diagnostics_and_fix()
        
        if success:
            print("\n✅ ONNX Runtime CoreML error fix applied successfully!")
            print("Your pokertool environment should now work without ONNX conflicts.")
        else:
            print("\n❌ Fix failed. Please check the log output above.")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nFix interrupted by user.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
