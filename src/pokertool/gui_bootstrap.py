#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Bootstrap helpers for launching the enhanced GUI safely."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Dict, Iterable, List, Tuple
import logging
import platform


logger = logging.getLogger(__name__)


DependencySpec = Tuple[str, str]


CORE_DEPENDENCIES: Tuple[DependencySpec, ...] = (
    ('cv2', 'opencv-python'),
    ('PIL', 'Pillow'),
    ('pytesseract', 'pytesseract'),
    ('mss', 'mss'),
    ('numpy', 'numpy'),
    ('requests', 'requests'),
    ('websocket', 'websocket-client'),
)

OPTIONAL_DEPENDENCIES: Tuple[DependencySpec, ...] = (
    ('keyboard', 'keyboard'),
    ('pyautogui', 'pyautogui'),
    ('redis', 'redis'),
)

MAC_EXTRAS: Tuple[DependencySpec, ...] = (
    ('Quartz', 'pyobjc-framework-Quartz'),
)


@dataclass(frozen=True)
class BootstrapReport:
    """Summary of dependency checks for the enhanced GUI."""

    missing: List[str]
    optional_missing: List[str]

    def is_ready(self) -> bool:
        """Return True when all required dependencies are present."""
        return not self.missing

    def as_dict(self) -> Dict[str, List[str]]:
        """Return a serialisable representation of the report."""
        return {
            'missing': list(self.missing),
            'optional_missing': list(self.optional_missing),
        }


def _resolve_specs() -> Tuple[DependencySpec, ...]:
    """Return the dependency specs including any platform extras."""
    specs: List[DependencySpec] = list(CORE_DEPENDENCIES)
    if platform.system().lower() == 'darwin':
        specs.extend(MAC_EXTRAS)
    return tuple(specs)


def _check_modules(specs: Iterable[DependencySpec]) -> Tuple[List[str], List[str]]:
    """Return lists of missing required and optional dependency packages."""
    missing: List[str] = []
    optional_missing: List[str] = []

    for module_name, package_name in specs:
        try:
            import_module(module_name)
        except Exception:  # pragma: no cover - import error branch is runtime specific
            missing.append(package_name)

    for module_name, package_name in OPTIONAL_DEPENDENCIES:
        try:
            import_module(module_name)
        except Exception:  # pragma: no cover - import error branch is runtime specific
            optional_missing.append(package_name)

    return missing, optional_missing


def bootstrap_enhanced_gui(raise_on_missing: bool = True) -> BootstrapReport:
    """
    Verify GUI runtime dependencies without mutating the environment.

    Args:
        raise_on_missing: When True, raise RuntimeError if required packages
            are not available. When False, return the report for the caller
            to decide how to proceed.
    """
    required_specs = _resolve_specs()
    missing, optional_missing = _check_modules(required_specs)
    report = BootstrapReport(missing=missing, optional_missing=optional_missing)

    if missing:
        logger.error(
            "Enhanced GUI dependencies missing: %s",
            ', '.join(sorted(set(missing))),
        )
        if raise_on_missing:
            raise RuntimeError(
                "Enhanced GUI dependencies missing. "
                "Install the packages listed above and retry."
            )

    if optional_missing:
        logger.info(
            "Optional GUI dependencies not available: %s",
            ', '.join(sorted(set(optional_missing))),
        )

    return report


__all__ = ['BootstrapReport', 'bootstrap_enhanced_gui']

