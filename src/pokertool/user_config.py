#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
User Configuration Management for PokerTool
============================================

Stores and manages user-specific settings like poker handle, preferences, etc.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class UserConfig:
    """User configuration settings."""

    # Poker identity
    poker_handle: Optional[str] = None
    poker_site: str = "BETFAIR"

    # Display preferences
    show_startup_validation: bool = True
    auto_detect_hero: bool = True

    # Advanced settings
    detection_confidence_threshold: float = 0.5
    enable_logging: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


class ConfigManager:
    """Manages user configuration persistence."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize config manager.

        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path is None:
            # Store in project root
            root = Path(__file__).resolve().parents[2]
            config_path = root / ".pokertool_config.json"

        self.config_path = config_path
        self._config: Optional[UserConfig] = None

    def load(self) -> UserConfig:
        """Load configuration from disk."""
        if self._config is not None:
            return self._config

        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._config = UserConfig.from_dict(data)
                logger.info(f"Loaded config from {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, using defaults")
                self._config = UserConfig()
        else:
            logger.info("No config file found, using defaults")
            self._config = UserConfig()

        return self._config

    def save(self, config: Optional[UserConfig] = None) -> None:
        """
        Save configuration to disk.

        Args:
            config: Config to save. If None, saves current config.
        """
        if config is not None:
            self._config = config

        if self._config is None:
            logger.warning("No config to save")
            return

        try:
            # Ensure parent directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config.to_dict(), f, indent=2)

            logger.info(f"Saved config to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get_poker_handle(self) -> Optional[str]:
        """Get the user's poker handle."""
        config = self.load()
        return config.poker_handle

    def set_poker_handle(self, handle: str) -> None:
        """
        Set the user's poker handle.

        Args:
            handle: Poker username/handle
        """
        config = self.load()
        config.poker_handle = handle
        self.save(config)
        logger.info(f"Updated poker handle: {handle}")

    def has_poker_handle(self) -> bool:
        """Check if poker handle is configured."""
        handle = self.get_poker_handle()
        return handle is not None and len(handle.strip()) > 0

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._config = UserConfig()
        self.save()
        logger.info("Reset configuration to defaults")


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_poker_handle() -> Optional[str]:
    """Convenience function to get poker handle."""
    return get_config_manager().get_poker_handle()


def set_poker_handle(handle: str) -> None:
    """Convenience function to set poker handle."""
    get_config_manager().set_poker_handle(handle)


def has_poker_handle() -> bool:
    """Convenience function to check if handle is configured."""
    return get_config_manager().has_poker_handle()


def prompt_for_poker_handle() -> Optional[str]:
    """
    Prompt user for their poker handle if not configured.

    Returns:
        The poker handle, or None if cancelled
    """
    manager = get_config_manager()

    if manager.has_poker_handle():
        handle = manager.get_poker_handle()
        print(f"\nCurrent poker handle: {handle}")
        response = input("Keep this handle? (Y/n): ").strip().lower()
        if response in ['', 'y', 'yes']:
            return handle

    print("\n" + "="*70)
    print("POKER HANDLE SETUP")
    print("="*70)
    print("\nTo accurately identify your position at the table, please enter")
    print("your poker username/handle exactly as it appears on the poker site.")
    print("\nExample: If you see 'JohnPoker123' at the table, enter: JohnPoker123")
    print("(Case-sensitive, no spaces)")
    print()

    while True:
        handle = input("Enter your poker handle (or 'skip' to skip): ").strip()

        if handle.lower() == 'skip':
            print("\n⚠ Skipped poker handle setup")
            print("Hero detection will use seat position heuristics (less accurate)")
            return None

        if not handle:
            print("❌ Handle cannot be empty. Try again or type 'skip'.")
            continue

        if len(handle) < 2:
            print("❌ Handle too short. Try again or type 'skip'.")
            continue

        # Confirm
        print(f"\nYou entered: {handle}")
        confirm = input("Is this correct? (Y/n): ").strip().lower()

        if confirm in ['', 'y', 'yes']:
            manager.set_poker_handle(handle)
            print(f"\n✓ Poker handle saved: {handle}")
            return handle
        else:
            print("Let's try again...")


if __name__ == '__main__':
    # Test the config system
    print("Testing UserConfig system...")

    manager = ConfigManager(Path("test_config.json"))

    # Test save/load
    config = UserConfig(poker_handle="TestPlayer123")
    manager.save(config)

    loaded = manager.load()
    assert loaded.poker_handle == "TestPlayer123"

    # Test convenience functions
    set_poker_handle("NewPlayer456")
    assert get_poker_handle() == "NewPlayer456"
    assert has_poker_handle() is True

    print("✓ All tests passed")

    # Cleanup
    Path("test_config.json").unlink(missing_ok=True)
