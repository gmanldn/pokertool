"""API Key Resolver - Resolve API keys from multiple sources with fallback"""
import os
import logging
from typing import Optional, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """AI provider types"""
    CLAUDE_CODE = "claude-code"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    OPENAI = "openai"


class APIKeyResolver:
    """Resolve API keys from environment variables and other sources"""

    # Map of provider to environment variable names (in order of preference)
    ENV_VAR_MAP: Dict[ProviderType, list[str]] = {
        ProviderType.CLAUDE_CODE: ["ANTHROPIC_API_KEY", "CLAUDE_API_KEY"],
        ProviderType.ANTHROPIC: ["ANTHROPIC_API_KEY", "CLAUDE_API_KEY"],
        ProviderType.OPENROUTER: ["OPENROUTER_API_KEY"],
        ProviderType.OPENAI: ["OPENAI_API_KEY"],
    }

    def __init__(self):
        self._cache: Dict[ProviderType, Optional[str]] = {}

    def get_key(self, provider: ProviderType, ui_key: Optional[str] = None) -> Optional[str]:
        """
        Get API key for provider with fallback priority:
        1. UI-provided key (from frontend)
        2. Environment variable
        3. Cached value

        Args:
            provider: The AI provider
            ui_key: Optional key from UI/frontend

        Returns:
            API key or None if not found
        """
        # Priority 1: UI provided key
        if ui_key:
            self._cache[provider] = ui_key
            return ui_key

        # Priority 2: Environment variable
        env_key = self._get_from_env(provider)
        if env_key:
            self._cache[provider] = env_key
            return env_key

        # Priority 3: Cached value
        if provider in self._cache:
            return self._cache[provider]

        logger.warning(f"No API key found for provider: {provider}")
        return None

    def _get_from_env(self, provider: ProviderType) -> Optional[str]:
        """Get API key from environment variables"""
        env_vars = self.ENV_VAR_MAP.get(provider, [])

        for var_name in env_vars:
            key = os.getenv(var_name)
            if key:
                logger.info(f"Found API key for {provider} in environment variable: {var_name}")
                return key

        return None

    def has_key(self, provider: ProviderType, ui_key: Optional[str] = None) -> bool:
        """Check if API key is available for provider"""
        return self.get_key(provider, ui_key) is not None

    def validate_key(self, key: str, provider: ProviderType) -> bool:
        """
        Basic validation of API key format

        Args:
            key: The API key to validate
            provider: The provider type

        Returns:
            True if key format is valid
        """
        if not key or len(key) < 10:
            return False

        # Provider-specific format validation
        if provider == ProviderType.ANTHROPIC or provider == ProviderType.CLAUDE_CODE:
            return key.startswith('sk-ant-')
        elif provider == ProviderType.OPENAI:
            return key.startswith('sk-')
        elif provider == ProviderType.OPENROUTER:
            return len(key) > 20  # OpenRouter keys don't have specific prefix

        return True

    def get_available_providers(self, ui_keys: Optional[Dict[str, str]] = None) -> list[ProviderType]:
        """
        Get list of providers with available API keys

        Args:
            ui_keys: Optional dict of provider -> key from UI

        Returns:
            List of providers with valid keys
        """
        available = []

        for provider in ProviderType:
            ui_key = ui_keys.get(provider.value) if ui_keys else None
            if self.has_key(provider, ui_key):
                available.append(provider)

        return available

    def clear_cache(self):
        """Clear cached API keys"""
        self._cache.clear()

    def set_cache(self, provider: ProviderType, key: str):
        """Manually set cached key for provider"""
        self._cache[provider] = key

    def get_source(self, provider: ProviderType, ui_key: Optional[str] = None) -> str:
        """
        Get the source of the API key (for debugging/logging)

        Returns:
            Source description (e.g., "UI", "ANTHROPIC_API_KEY", "cache", "not found")
        """
        if ui_key:
            return "UI"

        # Check environment
        env_vars = self.ENV_VAR_MAP.get(provider, [])
        for var_name in env_vars:
            if os.getenv(var_name):
                return var_name

        # Check cache
        if provider in self._cache:
            return "cache"

        return "not found"

    def log_key_sources(self):
        """Log which providers have keys and their sources"""
        logger.info("API Key Sources:")
        for provider in ProviderType:
            source = self.get_source(provider)
            status = "✓" if source != "not found" else "✗"
            logger.info(f"  {status} {provider.value}: {source}")


# Global singleton instance
api_key_resolver = APIKeyResolver()
