#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Utility helpers for loading enhanced GUI panel configuration."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict


logger = logging.getLogger(__name__)

CONFIG_ROOT = Path(__file__).resolve().parent.parent / 'assets' / 'gui_panels'


@lru_cache(maxsize=8)
def load_panel_config(name: str) -> Dict[str, object]:
    """Return configuration for the given panel name."""
    config_path = CONFIG_ROOT / f'{name}.json'
    if not config_path.exists():
        logger.debug('Panel config %s not found at %s', name, config_path)
        return {}

    try:
        with config_path.open('r', encoding='utf-8') as handle:
            data = json.load(handle)
            if isinstance(data, dict):
                return data
            logger.warning('Panel config %s is not a JSON object', name)
    except Exception as exc:  # pragma: no cover - IO errors are environment specific
        logger.error('Failed to load %s panel config: %s', name, exc)
    return {}


__all__ = ['load_panel_config']

