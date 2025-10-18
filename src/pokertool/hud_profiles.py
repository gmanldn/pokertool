"""HUD profile storage helpers."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Any

from .storage import get_secure_db

logger = logging.getLogger(__name__)

PROFILE_DIR = Path.home() / ".pokertool" / "hud_profiles"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

_secure_db = None


def _get_secure_db():
    global _secure_db
    if _secure_db is None:
        _secure_db = get_secure_db()
    return _secure_db


def _migrate_legacy_profile(name: str) -> Dict[str, Any]:
    """Load a legacy file-based profile and migrate it into secure storage."""
    profile_path = PROFILE_DIR / f"{name}.json"
    if not profile_path.exists():
        return {}

    try:
        with profile_path.open('r', encoding='utf-8') as handle:
            data = json.load(handle)
    except Exception as exc:
        logger.warning("Failed to load legacy HUD profile %s: %s", name, exc)
        return {}

    try:
        _get_secure_db().save_hud_profile(name, data if isinstance(data, dict) else {})
        logger.info("Migrated HUD profile '%s' into secure storage", name)
    except Exception as exc:
        logger.error("Failed to migrate HUD profile %s: %s", name, exc)

    return data if isinstance(data, dict) else {}


def list_hud_profiles() -> List[str]:
    """Return the list of available HUD profile names."""
    try:
        return _get_secure_db().list_hud_profiles()
    except Exception as exc:
        logger.error("Listing HUD profiles via secure storage failed: %s", exc)
        profiles = [file.stem for file in PROFILE_DIR.glob('*.json')]
        if 'Default' not in profiles:
            profiles.append('Default')
        return sorted(set(profiles))


def load_hud_profile(name: str) -> Dict[str, Any]:
    """Load the HUD profile dictionary or return empty dict when missing."""
    try:
        data = _get_secure_db().load_hud_profile(name)
        if data:
            return data
    except Exception as exc:
        logger.error("Failed to load HUD profile %s from secure storage: %s", name, exc)

    # Fallback to legacy file and migrate if possible
    return _migrate_legacy_profile(name)


def save_hud_profile(name: str, config_dict: Dict[str, Any]) -> str:
    """Persist the HUD profile dictionary using secure storage."""
    _get_secure_db().save_hud_profile(name, config_dict)
    return f"secure-db://{Path(_get_secure_db().db_path).name}/hud_profiles/{name}"
