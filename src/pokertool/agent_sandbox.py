"""Sandbox Execution for AI Agents - Restrict file system access"""
import os
from pathlib import Path
from typing import Set, Optional

class AgentSandbox:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.allowed_paths: Set[Path] = {self.project_root}
    
    def is_path_allowed(self, path: str) -> bool:
        try:
            resolved = Path(path).resolve()
            return any(resolved.is_relative_to(allowed) for allowed in self.allowed_paths)
        except:
            return False
    
    def validate_file_operation(self, path: str, operation: str) -> Tuple[bool, Optional[str]]:
        if not self.is_path_allowed(path):
            return False, f"Access denied: {path} outside project directory"
        return True, None
    
    def add_allowed_path(self, path: str):
        self.allowed_paths.add(Path(path).resolve())
