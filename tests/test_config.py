"""Tests for centralized configuration management."""

import os
import tempfile
from pathlib import Path

import pytest

from src.pokertool.config import (
    AppConfig,
    DatabaseConfig,
    APIConfig,
    OCRConfig,
    MLConfig,
    StorageConfig,
    LoggingConfig,
    SecurityConfig,
    get_config,
    load_config,
    reset_config,
)


class TestDatabaseConfig:
    """Test DatabaseConfig."""

    def test_default_values(self):
        """Test database config has sensible defaults."""
        config = DatabaseConfig()
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.name == "pokertool"
        assert config.pool_size == 10

    def test_env_override(self):
        """Test environment variable override."""
        os.environ["DB_HOST"] = "prod.example.com"
        os.environ["DB_PORT"] = "5433"
        try:
            config = DatabaseConfig.from_env()
            assert config.host == "prod.example.com"
            assert config.port == 5433
        finally:
            del os.environ["DB_HOST"]
            del os.environ["DB_PORT"]


class TestAPIConfig:
    """Test APIConfig."""

    def test_default_values(self):
        """Test API config defaults."""
        config = APIConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.debug is False
        assert config.workers == 4

    def test_rate_limit(self):
        """Test rate limit configuration."""
        config = APIConfig(rate_limit=500)
        assert config.rate_limit == 500


class TestOCRConfig:
    """Test OCRConfig."""

    def test_default_values(self):
        """Test OCR config defaults."""
        config = OCRConfig()
        assert config.engine == "tesseract"
        assert config.confidence_threshold == 0.7
        assert config.cache_results is True

    def test_confidence_validation(self):
        """Test confidence threshold validation."""
        with pytest.raises(ValueError):
            OCRConfig(confidence_threshold=1.5)

        with pytest.raises(ValueError):
            OCRConfig(confidence_threshold=-0.1)

        # Valid values should work
        config = OCRConfig(confidence_threshold=0.5)
        assert config.confidence_threshold == 0.5


class TestMLConfig:
    """Test MLConfig."""

    def test_default_values(self):
        """Test ML config defaults."""
        config = MLConfig()
        assert config.enabled is True
        assert config.device == "cpu"
        assert config.batch_size == 32
        assert config.num_workers == 4

    def test_custom_device(self):
        """Test setting custom device."""
        config = MLConfig(device="cuda")
        assert config.device == "cuda"


class TestStorageConfig:
    """Test StorageConfig."""

    def test_default_values(self):
        """Test storage config defaults."""
        config = StorageConfig()
        assert config.type == "sqlite"
        assert config.path == "pokertool.db"
        assert config.auto_backup is True
        assert config.backup_interval == 3600

    def test_encryption(self):
        """Test encryption configuration."""
        config = StorageConfig(encryption_key="secret123")
        assert config.encryption_key == "secret123"


class TestLoggingConfig:
    """Test LoggingConfig."""

    def test_default_values(self):
        """Test logging config defaults."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.format == "json"
        assert config.console is True
        assert config.file_enabled is True

    def test_custom_level(self):
        """Test setting custom log level."""
        config = LoggingConfig(level="DEBUG")
        assert config.level == "DEBUG"


class TestSecurityConfig:
    """Test SecurityConfig."""

    def test_default_values(self):
        """Test security config defaults."""
        config = SecurityConfig()
        assert config.api_key_required is True
        assert config.jwt_algorithm == "HS256"
        assert config.jwt_expiration == 3600

    def test_ssl_configuration(self):
        """Test SSL configuration."""
        config = SecurityConfig(
            ssl_enabled=True,
            ssl_cert="/path/to/cert.pem",
            ssl_key="/path/to/key.pem",
        )
        assert config.ssl_enabled is True
        assert config.ssl_cert == "/path/to/cert.pem"


class TestAppConfig:
    """Test main AppConfig."""

    def test_default_values(self):
        """Test app config has all subsections."""
        config = AppConfig()
        assert config.app_name == "PokerTool"
        assert config.environment == "development"
        assert config.debug is False

    def test_subsections(self):
        """Test all config subsections are present."""
        config = AppConfig()
        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.api, APIConfig)
        assert isinstance(config.ocr, OCRConfig)
        assert isinstance(config.ml, MLConfig)
        assert isinstance(config.storage, StorageConfig)
        assert isinstance(config.logging, LoggingConfig)
        assert isinstance(config.security, SecurityConfig)

    def test_custom_subsections(self):
        """Test passing custom subsections."""
        db_config = DatabaseConfig(host="custom.db")
        api_config = APIConfig(port=9000)

        config = AppConfig(database=db_config, api=api_config)
        assert config.database.host == "custom.db"
        assert config.api.port == 9000

    def test_production_environment(self):
        """Test production environment configuration."""
        config = AppConfig(environment="production", debug=False)
        assert config.environment == "production"
        assert config.debug is False


class TestConfigManagement:
    """Test configuration management functions."""

    def teardown_method(self):
        """Reset config after each test."""
        reset_config()

    def test_get_config_singleton(self):
        """Test get_config returns singleton."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_load_config(self):
        """Test load_config function."""
        reset_config()
        config = load_config()
        assert isinstance(config, AppConfig)
        assert config.app_name == "PokerTool"

    def test_load_config_with_env_file(self):
        """Test loading config from environment variables."""
        reset_config()

        os.environ["APP_ENVIRONMENT"] = "production"
        os.environ["API_PORT"] = "9000"
        os.environ["DB_HOST"] = "prod.db"

        try:
            config = load_config()
            # Config should be loaded (values depend on .env implementation)
            assert config is not None
            assert config.environment == "production"
        finally:
            del os.environ["APP_ENVIRONMENT"]
            del os.environ["API_PORT"]
            del os.environ["DB_HOST"]
            reset_config()

    def test_reset_config(self):
        """Test resetting config."""
        config1 = get_config()
        reset_config()
        config2 = get_config()
        assert config1 is not config2

    def test_config_json_export(self):
        """Test exporting config to JSON."""
        config = AppConfig()
        json_str = config.model_dump_json(indent=2)
        assert "PokerTool" in json_str
        assert "database" in json_str
        assert "api" in json_str


class TestConfigValidation:
    """Test configuration validation."""

    def test_invalid_ocr_confidence(self):
        """Test OCR confidence validation."""
        with pytest.raises(ValueError, match="confidence_threshold"):
            OCRConfig(confidence_threshold=2.0)

    def test_env_var_parsing(self):
        """Test environment variable parsing."""
        os.environ["API_PORT"] = "8001"
        os.environ["API_DEBUG"] = "true"
        try:
            config = APIConfig.from_env()
            assert config.port == 8001
            assert config.debug is True
        finally:
            del os.environ["API_PORT"]
            del os.environ["API_DEBUG"]

    def test_cors_configuration(self):
        """Test CORS configuration."""
        config = SecurityConfig(cors_origins="http://localhost:3000,http://localhost:3001")
        assert "localhost" in config.cors_origins


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
