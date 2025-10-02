"""HUD profile storage helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any

PROFILE_DIR = Path.home() / ".pokertool" / "hud_profiles"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)


def list_hud_profiles() -> List[str]:
    """Return the list of available HUD profile names."""
    profiles = []
    for file in PROFILE_DIR.glob('*.json'):
        profiles.append(file.stem)
    if 'Default' not in profiles:
        profiles.append('Default')
    return sorted(profiles)


def load_hud_profile(name: str) -> Dict[str, Any]:
    """Load the HUD profile dictionary or return empty dict when missing."""
    profile_path = PROFILE_DIR / f"{name}.json"
    if not profile_path.exists():
        return {}
    try:
        with profile_path.open('r') as handle:
            return json.load(handle)
    except Exception:
        return {}


def save_hud_profile(name: str, config_dict: Dict[str, Any]) -> Path:
    """Persist the HUD profile dictionary to disk."""
    profile_path = PROFILE_DIR / f"{name}.json"
    with profile_path.open('w') as handle:
        json.dump(config_dict, handle, indent=2)
    return profile_path

