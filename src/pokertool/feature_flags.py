"""
Feature Flags System for PokerTool

This module provides a centralized feature flag management system that allows
runtime toggling of features without code changes. Feature flags are controlled
via environment variables and can be used for:
- Gradual feature rollouts
- A/B testing
- Beta features
- Emergency feature disabling
- Environment-specific features

Usage:
    from pokertool.feature_flags import FeatureFlags

    flags = FeatureFlags()

    if flags.is_enabled('betfair_accuracy'):
        # Use new Betfair accuracy improvements
        pass

    if flags.is_enabled('multi_table', user_id='user123'):
        # Enable multi-table for specific user
        pass
"""

import os
import logging
from typing import Dict, Optional, Set, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import json


logger = logging.getLogger(__name__)


class FeatureState(Enum):
    """Feature flag states."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    BETA = "beta"
    DEPRECATED = "deprecated"


@dataclass
class Feature:
    """
    Represents a single feature flag.

    Attributes:
        name: Unique feature identifier (snake_case)
        enabled: Whether the feature is enabled
        description: Human-readable description
        state: Current state of the feature
        rollout_percentage: Percentage of users who see this feature (0-100)
        allowed_users: Set of user IDs allowed to use this feature
        allowed_environments: Environments where this feature is available
        dependencies: Other features this feature depends on
    """
    name: str
    enabled: bool = False
    description: str = ""
    state: FeatureState = FeatureState.DISABLED
    rollout_percentage: int = 0
    allowed_users: Set[str] = field(default_factory=set)
    allowed_environments: Set[str] = field(default_factory=set)
    dependencies: List[str] = field(default_factory=list)

    def is_available_for_user(self, user_id: Optional[str] = None) -> bool:
        """Check if feature is available for a specific user."""
        if not self.enabled:
            return False

        # If no user restrictions, available to all
        if not self.allowed_users:
            return True

        # Check if user is in allowed list
        return user_id in self.allowed_users if user_id else False

    def is_available_in_environment(self, environment: str) -> bool:
        """Check if feature is available in specific environment."""
        if not self.enabled:
            return False

        # If no environment restrictions, available in all
        if not self.allowed_environments:
            return True

        return environment in self.allowed_environments


class FeatureFlags:
    """
    Central feature flag management system.

    Reads feature flags from environment variables with the pattern:
    FEATURE_{FEATURE_NAME}=true|false

    Example environment variables:
        FEATURE_BETFAIR_ACCURACY=true
        FEATURE_MULTI_TABLE=false
        FEATURE_VOICE_COMMANDS=beta
    """

    # Default feature definitions
    DEFAULT_FEATURES = {
        'betfair_accuracy': Feature(
            name='betfair_accuracy',
            enabled=True,
            description='Betfair scraping accuracy improvements',
            state=FeatureState.ENABLED,
        ),
        'health_monitor': Feature(
            name='health_monitor',
            enabled=True,
            description='System health monitor dashboard',
            state=FeatureState.ENABLED,
        ),
        'active_learning': Feature(
            name='active_learning',
            enabled=True,
            description='Active learning feedback loop',
            state=FeatureState.ENABLED,
        ),
        'model_calibration': Feature(
            name='model_calibration',
            enabled=True,
            description='Model calibration system',
            state=FeatureState.ENABLED,
        ),
        'opponent_fusion': Feature(
            name='opponent_fusion',
            enabled=True,
            description='Sequential opponent fusion',
            state=FeatureState.ENABLED,
        ),
        'multi_table': Feature(
            name='multi_table',
            enabled=False,
            description='Multi-table support (beta)',
            state=FeatureState.BETA,
        ),
        'voice_commands': Feature(
            name='voice_commands',
            enabled=False,
            description='Voice commands (in development)',
            state=FeatureState.DISABLED,
        ),
        'hand_replay': Feature(
            name='hand_replay',
            enabled=True,
            description='Hand replay system',
            state=FeatureState.ENABLED,
        ),
        'gamification': Feature(
            name='gamification',
            enabled=True,
            description='Gamification (badges, achievements)',
            state=FeatureState.ENABLED,
        ),
        'community': Feature(
            name='community',
            enabled=False,
            description='Community features (sharing, forums)',
            state=FeatureState.DISABLED,
        ),
    }

    def __init__(self, environment: Optional[str] = None):
        """
        Initialize feature flags system.

        Args:
            environment: Current environment (development, production, test).
                        If not provided, reads from NODE_ENV or PYTHON_ENV.
        """
        self.environment = environment or self._detect_environment()
        self.features: Dict[str, Feature] = {}
        self._load_features()
        self._log_feature_status()

    def _detect_environment(self) -> str:
        """Detect current environment from environment variables."""
        return os.getenv('NODE_ENV') or os.getenv('PYTHON_ENV', 'development')

    def _load_features(self) -> None:
        """Load features from environment variables and defaults."""
        # Start with default features
        self.features = self.DEFAULT_FEATURES.copy()

        # Override with environment variables
        for key, value in os.environ.items():
            if key.startswith('FEATURE_'):
                feature_name = key[8:].lower()  # Remove 'FEATURE_' prefix
                enabled = self._parse_bool(value)

                if feature_name in self.features:
                    # Update existing feature
                    self.features[feature_name].enabled = enabled
                    logger.info(f"Feature '{feature_name}' set to {enabled} from environment")
                else:
                    # Create new feature from environment variable
                    self.features[feature_name] = Feature(
                        name=feature_name,
                        enabled=enabled,
                        description=f"Feature flag from environment: {key}",
                    )
                    logger.info(f"New feature '{feature_name}' created from environment: {enabled}")

    def _parse_bool(self, value: str) -> bool:
        """Parse boolean value from string."""
        return value.lower() in ('true', '1', 'yes', 'on', 'enabled')

    def _log_feature_status(self) -> None:
        """Log the status of all features at startup."""
        enabled_features = [f.name for f in self.features.values() if f.enabled]
        disabled_features = [f.name for f in self.features.values() if not f.enabled]

        logger.info(f"Feature flags initialized in '{self.environment}' environment")
        logger.info(f"Enabled features ({len(enabled_features)}): {', '.join(enabled_features)}")
        logger.debug(f"Disabled features ({len(disabled_features)}): {', '.join(disabled_features)}")

    def is_enabled(
        self,
        feature_name: str,
        user_id: Optional[str] = None,
        default: bool = False
    ) -> bool:
        """
        Check if a feature is enabled.

        Args:
            feature_name: Name of the feature to check (snake_case)
            user_id: Optional user ID for user-specific features
            default: Default value if feature not found

        Returns:
            True if feature is enabled, False otherwise

        Example:
            if flags.is_enabled('betfair_accuracy'):
                use_new_accuracy_module()
        """
        feature = self.features.get(feature_name)

        if feature is None:
            logger.warning(f"Unknown feature flag: '{feature_name}', using default: {default}")
            return default

        # Check basic enabled status
        if not feature.enabled:
            return False

        # Check environment restrictions
        if not feature.is_available_in_environment(self.environment):
            logger.debug(f"Feature '{feature_name}' not available in '{self.environment}' environment")
            return False

        # Check user restrictions
        if not feature.is_available_for_user(user_id):
            logger.debug(f"Feature '{feature_name}' not available for user '{user_id}'")
            return False

        # Check dependencies
        for dependency in feature.dependencies:
            if not self.is_enabled(dependency, user_id=user_id):
                logger.debug(f"Feature '{feature_name}' disabled due to dependency '{dependency}'")
                return False

        return True

    def get_feature(self, feature_name: str) -> Optional[Feature]:
        """Get feature object by name."""
        return self.features.get(feature_name)

    def get_all_features(self) -> Dict[str, Feature]:
        """Get all feature flags."""
        return self.features.copy()

    def get_enabled_features(self) -> List[str]:
        """Get list of all enabled feature names."""
        return [name for name, feature in self.features.items() if feature.enabled]

    def get_disabled_features(self) -> List[str]:
        """Get list of all disabled feature names."""
        return [name for name, feature in self.features.items() if not feature.enabled]

    def enable_feature(self, feature_name: str) -> None:
        """
        Enable a feature at runtime.

        Note: This change is not persisted to environment variables.
        For permanent changes, update .env file.
        """
        if feature_name in self.features:
            self.features[feature_name].enabled = True
            logger.info(f"Feature '{feature_name}' enabled at runtime")
        else:
            logger.warning(f"Attempted to enable unknown feature: '{feature_name}'")

    def disable_feature(self, feature_name: str) -> None:
        """
        Disable a feature at runtime.

        Note: This change is not persisted to environment variables.
        For permanent changes, update .env file.
        """
        if feature_name in self.features:
            self.features[feature_name].enabled = False
            logger.info(f"Feature '{feature_name}' disabled at runtime")
        else:
            logger.warning(f"Attempted to disable unknown feature: '{feature_name}'")

    def register_feature(
        self,
        name: str,
        enabled: bool = False,
        description: str = "",
        state: FeatureState = FeatureState.DISABLED,
        dependencies: Optional[List[str]] = None
    ) -> None:
        """
        Register a new feature flag at runtime.

        Args:
            name: Unique feature identifier
            enabled: Initial enabled state
            description: Human-readable description
            state: Feature state
            dependencies: List of feature names this feature depends on
        """
        if name in self.features:
            logger.warning(f"Feature '{name}' already exists, updating...")

        self.features[name] = Feature(
            name=name,
            enabled=enabled,
            description=description,
            state=state,
            dependencies=dependencies or []
        )
        logger.info(f"Feature '{name}' registered: enabled={enabled}")

    def to_dict(self) -> Dict[str, bool]:
        """
        Export all feature flags as a simple dictionary.

        Returns:
            Dictionary mapping feature names to enabled status
        """
        return {name: feature.enabled for name, feature in self.features.items()}

    def to_json(self) -> str:
        """
        Export all feature flags as JSON.

        Returns:
            JSON string with all feature information
        """
        export_data = {
            'environment': self.environment,
            'features': {
                name: {
                    'enabled': feature.enabled,
                    'description': feature.description,
                    'state': feature.state.value,
                    'rollout_percentage': feature.rollout_percentage,
                }
                for name, feature in self.features.items()
            }
        }
        return json.dumps(export_data, indent=2)


# Global instance for easy access
_global_flags: Optional[FeatureFlags] = None


def get_feature_flags() -> FeatureFlags:
    """
    Get the global FeatureFlags instance (singleton pattern).

    Returns:
        Global FeatureFlags instance

    Example:
        from pokertool.feature_flags import get_feature_flags

        flags = get_feature_flags()
        if flags.is_enabled('betfair_accuracy'):
            use_new_module()
    """
    global _global_flags

    if _global_flags is None:
        _global_flags = FeatureFlags()

    return _global_flags


def reset_feature_flags() -> None:
    """Reset the global feature flags instance (mainly for testing)."""
    global _global_flags
    _global_flags = None


def is_feature_enabled(feature_name: str, user_id: Optional[str] = None, default: bool = False) -> bool:
    """
    Convenience function to check if a feature is enabled.

    This is a shortcut for get_feature_flags().is_enabled(...)

    Args:
        feature_name: Name of the feature
        user_id: Optional user ID
        default: Default value if feature not found

    Returns:
        True if feature is enabled, False otherwise

    Example:
        from pokertool.feature_flags import is_feature_enabled

        if is_feature_enabled('betfair_accuracy'):
            use_new_accuracy_module()
    """
    return get_feature_flags().is_enabled(feature_name, user_id=user_id, default=default)


# Feature flag decorators
def requires_feature(feature_name: str, default_return=None):
    """
    Decorator that only executes function if feature is enabled.

    Args:
        feature_name: Name of the required feature
        default_return: Value to return if feature is disabled

    Example:
        @requires_feature('voice_commands')
        def process_voice_command(text: str) -> str:
            return parse_voice_command(text)
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            if is_feature_enabled(feature_name):
                return func(*args, **kwargs)
            else:
                logger.debug(f"Function '{func.__name__}' skipped: feature '{feature_name}' disabled")
                return default_return
        return wrapper
    return decorator


# Example usage and testing
if __name__ == '__main__':
    # Configure logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create feature flags instance
    flags = FeatureFlags()

    # Check some features
    print("\n=== Feature Status ===")
    print(f"Betfair Accuracy: {flags.is_enabled('betfair_accuracy')}")
    print(f"Multi-table: {flags.is_enabled('multi_table')}")
    print(f"Voice Commands: {flags.is_enabled('voice_commands')}")

    # Get all enabled features
    print(f"\nEnabled features: {flags.get_enabled_features()}")

    # Export to JSON
    print("\n=== JSON Export ===")
    print(flags.to_json())

    # Test decorator
    @requires_feature('voice_commands', default_return="Feature disabled")
    def test_voice_feature():
        return "Voice command processed!"

    print(f"\nVoice feature test: {test_voice_feature()}")

    # Enable feature at runtime
    flags.enable_feature('voice_commands')
    print(f"After enabling: {test_voice_feature()}")
