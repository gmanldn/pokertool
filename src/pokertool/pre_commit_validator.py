"""Pre-commit Validation - Run linters, formatters, type checkers"""
import subprocess
from typing import List, Tuple

class PreCommitValidator:
    def __init__(self):
        self.validators = [
            ("black", ["black", "--check", "."]),
            ("mypy", ["mypy", "src"]),
            ("flake8", ["flake8", "src"]),
        ]
    
    def validate_all(self) -> Tuple[bool, List[str]]:
        errors = []
        for name, cmd in self.validators:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    errors.append(f"{name}: {result.stdout + result.stderr}")
            except Exception as e:
                errors.append(f"{name}: {str(e)}")
        return len(errors) == 0, errors
    
    def run_formatters(self) -> bool:
        try:
            subprocess.run(["black", "src"], check=True, timeout=30)
            return True
        except:
            return False
