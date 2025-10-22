"""
Cross-platform path utilities for PokerTool.

This module provides utilities to ensure consistent cross-platform
path handling using pathlib.Path instead of os.path.
"""

from pathlib import Path
from typing import Union
import os


def ensure_path(path: Union[str, Path]) -> Path:
    """
    Convert string paths to Path objects.
    
    Args:
        path: String or Path object
        
    Returns:
        Path: Pathlib Path object
        
    Example:
        >>> p = ensure_path("~/.pokertool/data")
        >>> p.exists()
    """
    if isinstance(path, str):
        # Expand user home directory (~)
        if path.startswith("~"):
            return Path(path).expanduser()
        return Path(path)
    return path


def ensure_dir(path: Union[str, Path], parents: bool = True) -> Path:
    """
    Ensure directory exists, creating it if necessary.
    
    Args:
        path: Directory path (string or Path)
        parents: Create parent directories if needed
        
    Returns:
        Path: Path object for the directory
        
    Example:
        >>> data_dir = ensure_dir("~/.pokertool/logs")
        >>> data_dir.exists()
        True
    """
    path = ensure_path(path)
    path.mkdir(parents=parents, exist_ok=True)
    return path


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path: Project root directory
    """
    # Navigate up from this file to project root
    return Path(__file__).parent.parent.parent


def get_data_dir() -> Path:
    """
    Get the user data directory for PokerTool.
    
    Returns:
        Path: ~/.pokertool/ directory
    """
    data_dir = Path.home() / ".pokertool"
    return ensure_dir(data_dir)


def get_logs_dir() -> Path:
    """
    Get the logs directory.
    
    Returns:
        Path: logs/ directory in project root
    """
    logs_dir = get_project_root() / "logs"
    return ensure_dir(logs_dir)


def get_config_dir() -> Path:
    """
    Get the configuration directory.
    
    Returns:
        Path: ~/.pokertool/config/ directory
    """
    config_dir = get_data_dir() / "config"
    return ensure_dir(config_dir)


def safe_file_path(filename: str, base_dir: Union[str, Path]) -> Path:
    """
    Create a safe file path, preventing directory traversal.
    
    Args:
        filename: Filename (without path separators)
        base_dir: Base directory to constrain the path to
        
    Returns:
        Path: Safe path within base_dir
        
    Raises:
        ValueError: If filename contains path separators or attempts traversal
        
    Example:
        >>> safe_file_path("data.json", "/var/app")
        Path('/var/app/data.json')
        >>> safe_file_path("../etc/passwd", "/var/app")  # Raises ValueError
    """
    # Check for path separators
    if os.sep in filename or "/" in filename or "\\" in filename:
        raise ValueError(f"Filename cannot contain path separators: {filename}")
    
    # Check for directory traversal attempts
    if ".." in filename:
        raise ValueError(f"Filename cannot contain '..': {filename}")
    
    base = ensure_path(base_dir)
    file_path = base / filename
    
    # Ensure resolved path is within base directory
    try:
        file_path.resolve().relative_to(base.resolve())
    except ValueError:
        raise ValueError(f"Path traversal detected: {filename}")
    
    return file_path
