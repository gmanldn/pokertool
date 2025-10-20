"""
Tests for the feature flags system.

Run with:
    pytest tests/test_feature_flags.py -v
"""

import os
import pytest
from unittest.mock import patch
from pokertool.feature_flags import (
    FeatureFlags,
    Feature,
    FeatureState,
    get_feature_flags,
    reset_feature_flags,
    is_feature_enabled,
    requires_feature,
)


class TestFeature:
    """Tests for the Feature class."""

    def test_feature_creation(self):
        """Test creating a basic feature."""
        feature = Feature(
            name='test_feature',
            enabled=True,
            description='Test feature',
        )
        assert feature.name == 'test_feature'
        assert feature.enabled is True
        assert feature.description == 'Test feature'
        assert feature.state == FeatureState.DISABLED  # default

    def test_feature_user_availability_no_restrictions(self):
        """Test feature availability when no user restrictions."""
        feature = Feature(name='test', enabled=True)
        assert feature.is_available_for_user() is True
        assert feature.is_available_for_user('user123') is True

    def test_feature_user_availability_with_restrictions(self):
        """Test feature availability with user restrictions."""
        feature = Feature(
            name='test',
            enabled=True,
            allowed_users={'user1', 'user2'}
        )
        assert feature.is_available_for_user('user1') is True
        assert feature.is_available_for_user('user2') is True
        assert feature.is_available_for_user('user3') is False
        assert feature.is_available_for_user() is False  # No user ID

    def test_feature_environment_availability_no_restrictions(self):
        """Test feature availability when no environment restrictions."""
        feature = Feature(name='test', enabled=True)
        assert feature.is_available_in_environment('development') is True
        assert feature.is_available_in_environment('production') is True

    def test_feature_environment_availability_with_restrictions(self):
        """Test feature availability with environment restrictions."""
        feature = Feature(
            name='test',
            enabled=True,
            allowed_environments={'development', 'test'}
        )
        assert feature.is_available_in_environment('development') is True
        assert feature.is_available_in_environment('test') is True
        assert feature.is_available_in_environment('production') is False

    def test_disabled_feature_not_available(self):
        """Test that disabled features are never available."""
        feature = Feature(
            name='test',
            enabled=False,
            allowed_users={'user1'}
        )
        assert feature.is_available_for_user('user1') is False
        assert feature.is_available_in_environment('development') is False


class TestFeatureFlags:
    """Tests for the FeatureFlags class."""

    def setup_method(self):
        """Reset environment before each test."""
        # Clear any FEATURE_* environment variables
        for key in list(os.environ.keys()):
            if key.startswith('FEATURE_'):
                del os.environ[key]

    def test_initialization_default_features(self):
        """Test that default features are loaded on initialization."""
        flags = FeatureFlags()

        # Check some default features exist
        assert 'betfair_accuracy' in flags.features
        assert 'health_monitor' in flags.features
        assert 'multi_table' in flags.features

    def test_initialization_from_environment(self):
        """Test loading features from environment variables."""
        # Set environment variables
        os.environ['FEATURE_CUSTOM_FEATURE'] = 'true'
        os.environ['FEATURE_ANOTHER_FEATURE'] = 'false'

        flags = FeatureFlags()

        assert 'custom_feature' in flags.features
        assert flags.features['custom_feature'].enabled is True
        assert 'another_feature' in flags.features
        assert flags.features['another_feature'].enabled is False

    def test_environment_variable_overrides_default(self):
        """Test that environment variables override default feature values."""
        # Explicitly disable via environment
        os.environ['FEATURE_MULTI_TABLE'] = 'false'
        flags_default = FeatureFlags()
        assert flags_default.is_enabled('multi_table') is False

        # Enable via environment
        os.environ['FEATURE_MULTI_TABLE'] = 'true'
        flags_override = FeatureFlags()
        assert flags_override.is_enabled('multi_table') is True

    def test_parse_bool_values(self):
        """Test parsing various boolean string values."""
        flags = FeatureFlags()

        assert flags._parse_bool('true') is True
        assert flags._parse_bool('True') is True
        assert flags._parse_bool('TRUE') is True
        assert flags._parse_bool('1') is True
        assert flags._parse_bool('yes') is True
        assert flags._parse_bool('on') is True
        assert flags._parse_bool('enabled') is True

        assert flags._parse_bool('false') is False
        assert flags._parse_bool('0') is False
        assert flags._parse_bool('no') is False
        assert flags._parse_bool('off') is False

    def test_is_enabled_basic(self):
        """Test basic feature enabled check."""
        # Explicitly set multi_table to false to ensure predictable test
        os.environ['FEATURE_MULTI_TABLE'] = 'false'
        flags = FeatureFlags()

        # betfair_accuracy is enabled by default
        assert flags.is_enabled('betfair_accuracy') is True

        # multi_table is explicitly disabled
        assert flags.is_enabled('multi_table') is False

    def test_is_enabled_unknown_feature_default(self):
        """Test checking unknown feature with default value."""
        flags = FeatureFlags()

        # Unknown feature returns provided default
        assert flags.is_enabled('unknown_feature', default=True) is True
        assert flags.is_enabled('unknown_feature', default=False) is False

    def test_is_enabled_with_user_restrictions(self):
        """Test feature check with user restrictions."""
        flags = FeatureFlags()

        # Register feature with user restrictions
        flags.register_feature(
            name='user_restricted',
            enabled=True,
        )
        flags.features['user_restricted'].allowed_users = {'user1', 'user2'}

        assert flags.is_enabled('user_restricted', user_id='user1') is True
        assert flags.is_enabled('user_restricted', user_id='user3') is False

    def test_is_enabled_with_environment_restrictions(self):
        """Test feature check with environment restrictions."""
        flags = FeatureFlags(environment='production')

        # Register feature available only in development
        flags.register_feature(
            name='dev_only',
            enabled=True,
        )
        flags.features['dev_only'].allowed_environments = {'development'}

        assert flags.is_enabled('dev_only') is False

        # Same feature in development environment
        flags_dev = FeatureFlags(environment='development')
        flags_dev.register_feature(
            name='dev_only',
            enabled=True,
        )
        flags_dev.features['dev_only'].allowed_environments = {'development'}

        assert flags_dev.is_enabled('dev_only') is True

    def test_is_enabled_with_dependencies(self):
        """Test feature with dependencies."""
        flags = FeatureFlags()

        # Register base feature
        flags.register_feature('base_feature', enabled=True)

        # Register dependent feature
        flags.register_feature(
            'dependent_feature',
            enabled=True,
            dependencies=['base_feature']
        )

        # Both enabled - dependent should work
        assert flags.is_enabled('dependent_feature') is True

        # Disable base feature
        flags.disable_feature('base_feature')

        # Dependent feature should now be disabled
        assert flags.is_enabled('dependent_feature') is False

    def test_enable_disable_feature(self):
        """Test runtime enable/disable of features."""
        flags = FeatureFlags()

        # Register disabled feature
        flags.register_feature('test_feature', enabled=False)
        assert flags.is_enabled('test_feature') is False

        # Enable at runtime
        flags.enable_feature('test_feature')
        assert flags.is_enabled('test_feature') is True

        # Disable at runtime
        flags.disable_feature('test_feature')
        assert flags.is_enabled('test_feature') is False

    def test_register_feature(self):
        """Test registering new features at runtime."""
        flags = FeatureFlags()

        flags.register_feature(
            name='new_feature',
            enabled=True,
            description='A new feature',
            state=FeatureState.BETA,
            dependencies=['betfair_accuracy']
        )

        feature = flags.get_feature('new_feature')
        assert feature is not None
        assert feature.name == 'new_feature'
        assert feature.enabled is True
        assert feature.description == 'A new feature'
        assert feature.state == FeatureState.BETA
        assert 'betfair_accuracy' in feature.dependencies

    def test_get_enabled_disabled_features(self):
        """Test getting lists of enabled/disabled features."""
        flags = FeatureFlags()

        enabled = flags.get_enabled_features()
        disabled = flags.get_disabled_features()

        # Should have some enabled and some disabled
        assert len(enabled) > 0
        assert len(disabled) > 0

        # Lists should be mutually exclusive
        assert set(enabled).isdisjoint(set(disabled))

        # All features should be in one list or the other
        all_features = set(enabled) | set(disabled)
        assert all_features == set(flags.features.keys())

    def test_to_dict(self):
        """Test exporting features to dictionary."""
        # Explicitly set multi_table to false
        os.environ['FEATURE_MULTI_TABLE'] = 'false'
        flags = FeatureFlags()

        feature_dict = flags.to_dict()

        assert isinstance(feature_dict, dict)
        assert 'betfair_accuracy' in feature_dict
        assert feature_dict['betfair_accuracy'] is True  # Default enabled
        assert 'multi_table' in feature_dict
        assert feature_dict['multi_table'] is False  # Explicitly disabled

    def test_to_json(self):
        """Test exporting features to JSON."""
        import json

        flags = FeatureFlags()
        json_str = flags.to_json()

        assert isinstance(json_str, str)

        # Parse and verify
        data = json.loads(json_str)
        assert 'environment' in data
        assert 'features' in data
        assert 'betfair_accuracy' in data['features']


class TestGlobalFeatureFlags:
    """Tests for global feature flags functions."""

    def setup_method(self):
        """Reset global instance before each test."""
        reset_feature_flags()

    def test_get_feature_flags_singleton(self):
        """Test that get_feature_flags returns singleton instance."""
        flags1 = get_feature_flags()
        flags2 = get_feature_flags()

        assert flags1 is flags2  # Same instance

    def test_reset_feature_flags(self):
        """Test resetting global instance."""
        # Ensure multi_table is disabled via environment
        os.environ['FEATURE_MULTI_TABLE'] = 'false'

        flags1 = get_feature_flags()
        flags1.enable_feature('multi_table')

        reset_feature_flags()

        flags2 = get_feature_flags()
        assert flags1 is not flags2  # Different instance
        # multi_table should be back to explicitly set default (disabled)
        assert flags2.is_enabled('multi_table') is False

    def test_is_feature_enabled_convenience_function(self):
        """Test convenience function for checking features."""
        # Use environment variable to enable
        os.environ['FEATURE_TEST_CONVENIENCE'] = 'true'

        # Reset to pick up new env var
        reset_feature_flags()

        assert is_feature_enabled('test_convenience') is True
        assert is_feature_enabled('nonexistent', default=True) is True


class TestFeatureFlagDecorator:
    """Tests for the requires_feature decorator."""

    def setup_method(self):
        """Reset before each test."""
        reset_feature_flags()

    def test_decorator_with_enabled_feature(self):
        """Test decorator with enabled feature."""
        # Enable feature via environment
        os.environ['FEATURE_DECORATOR_TEST'] = 'true'
        reset_feature_flags()

        @requires_feature('decorator_test')
        def test_function():
            return "executed"

        result = test_function()
        assert result == "executed"

    def test_decorator_with_disabled_feature(self):
        """Test decorator with disabled feature."""
        # Feature doesn't exist, so will be disabled

        @requires_feature('nonexistent_feature')
        def test_function():
            return "executed"

        result = test_function()
        assert result is None  # Default return

    def test_decorator_with_custom_default_return(self):
        """Test decorator with custom default return value."""

        @requires_feature('nonexistent_feature', default_return="feature disabled")
        def test_function():
            return "executed"

        result = test_function()
        assert result == "feature disabled"

    def test_decorator_with_arguments(self):
        """Test decorator on function with arguments."""
        os.environ['FEATURE_ARG_TEST'] = 'true'
        reset_feature_flags()

        @requires_feature('arg_test')
        def add_numbers(a: int, b: int) -> int:
            return a + b

        result = add_numbers(2, 3)
        assert result == 5


class TestEnvironmentDetection:
    """Tests for environment detection."""

    def test_detect_from_node_env(self):
        """Test detecting environment from NODE_ENV."""
        os.environ['NODE_ENV'] = 'production'

        flags = FeatureFlags()
        assert flags.environment == 'production'

    def test_detect_from_python_env(self):
        """Test detecting environment from PYTHON_ENV."""
        # Clear NODE_ENV if set
        os.environ.pop('NODE_ENV', None)
        os.environ['PYTHON_ENV'] = 'test'

        flags = FeatureFlags()
        assert flags.environment == 'test'

    def test_default_environment(self):
        """Test default environment when no env vars set."""
        os.environ.pop('NODE_ENV', None)
        os.environ.pop('PYTHON_ENV', None)

        flags = FeatureFlags()
        assert flags.environment == 'development'

    def test_explicit_environment(self):
        """Test explicitly setting environment."""
        flags = FeatureFlags(environment='custom')
        assert flags.environment == 'custom'


class TestFeatureIntegration:
    """Integration tests for feature flags."""

    def setup_method(self):
        """Setup for integration tests."""
        reset_feature_flags()
        for key in list(os.environ.keys()):
            if key.startswith('FEATURE_'):
                del os.environ[key]

    def test_full_workflow(self):
        """Test complete workflow of feature flag usage."""
        # 1. Set environment variables
        os.environ['FEATURE_NEW_ALGORITHM'] = 'true'
        os.environ['FEATURE_BETA_UI'] = 'false'

        # 2. Initialize flags
        flags = FeatureFlags()

        # 3. Check default features
        assert flags.is_enabled('betfair_accuracy') is True

        # 4. Check environment-based features
        assert flags.is_enabled('new_algorithm') is True
        assert flags.is_enabled('beta_ui') is False

        # 5. Register new feature at runtime
        flags.register_feature(
            name='runtime_feature',
            enabled=True,
            description='Added at runtime'
        )
        assert flags.is_enabled('runtime_feature') is True

        # 6. Toggle features
        flags.disable_feature('new_algorithm')
        assert flags.is_enabled('new_algorithm') is False

        # 7. Export state
        state_dict = flags.to_dict()
        assert 'runtime_feature' in state_dict
        assert 'new_algorithm' in state_dict

    def test_gradual_rollout_simulation(self):
        """Simulate gradual feature rollout to users."""
        flags = FeatureFlags()

        # Register feature with user restrictions (simulating gradual rollout)
        flags.register_feature('rollout_feature', enabled=True)

        # Phase 1: Internal users only
        flags.features['rollout_feature'].allowed_users = {'internal_user1', 'internal_user2'}

        assert flags.is_enabled('rollout_feature', user_id='internal_user1') is True
        assert flags.is_enabled('rollout_feature', user_id='external_user') is False

        # Phase 2: Open to all users
        flags.features['rollout_feature'].allowed_users = set()

        assert flags.is_enabled('rollout_feature', user_id='internal_user1') is True
        assert flags.is_enabled('rollout_feature', user_id='external_user') is True

    def test_environment_specific_features(self):
        """Test features that are environment-specific."""
        # Development environment
        dev_flags = FeatureFlags(environment='development')
        dev_flags.register_feature('debug_panel', enabled=True)
        dev_flags.features['debug_panel'].allowed_environments = {'development', 'test'}

        assert dev_flags.is_enabled('debug_panel') is True

        # Production environment
        prod_flags = FeatureFlags(environment='production')
        prod_flags.register_feature('debug_panel', enabled=True)
        prod_flags.features['debug_panel'].allowed_environments = {'development', 'test'}

        assert prod_flags.is_enabled('debug_panel') is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
