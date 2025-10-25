"""
Centralized configuration management for PokerTool.

Uses Pydantic v2 for validation and supports environment variable overrides.
Supports .env files and environment variables with type safety.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class DatabaseConfig(BaseModel):
    """Database configuration."""

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="pokertool", description="Database name")
    user: str = Field(default="postgres", description="Database user")
    password: str = Field(default="", description="Database password")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max connections above pool size")
    pool_timeout: int = Field(default=30, description="Connection pool timeout in seconds")
    echo: bool = Field(default=False, description="Echo SQL queries")

    @classmethod
    def from_env(cls):
        """Create from environment variables."""
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            name=os.getenv("DB_NAME", "pokertool"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
        )


class APIConfig(BaseModel):
    """API configuration."""

    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Log level")
    workers: int = Field(default=4, description="Number of workers")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_connections: int = Field(default=100, description="Max concurrent connections")
    rate_limit: int = Field(default=1000, description="Requests per minute")

    @classmethod
    def from_env(cls):
        """Create from environment variables."""
        return cls(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000")),
            debug=os.getenv("API_DEBUG", "false").lower() == "true",
            log_level=os.getenv("API_LOG_LEVEL", "INFO"),
            workers=int(os.getenv("API_WORKERS", "4")),
            timeout=int(os.getenv("API_TIMEOUT", "30")),
            max_connections=int(os.getenv("API_MAX_CONNECTIONS", "100")),
            rate_limit=int(os.getenv("API_RATE_LIMIT", "1000")),
        )


class OCRConfig(BaseModel):
    """OCR configuration."""

    engine: str = Field(default="tesseract", description="OCR engine: tesseract, easyocr, paddleocr")
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence score")
    languages: str = Field(default="en", description="Languages to recognize")
    cache_results: bool = Field(default=True, description="Cache OCR results")
    use_gpu: bool = Field(default=False, description="Use GPU acceleration")

    @field_validator("confidence_threshold")
    @classmethod
    def validate_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("confidence_threshold must be between 0 and 1")
        return v

    @classmethod
    def from_env(cls):
        """Create from environment variables."""
        return cls(
            engine=os.getenv("OCR_ENGINE", "tesseract"),
            confidence_threshold=float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.7")),
            languages=os.getenv("OCR_LANGUAGES", "en"),
            cache_results=os.getenv("OCR_CACHE_RESULTS", "true").lower() == "true",
            use_gpu=os.getenv("OCR_USE_GPU", "false").lower() == "true",
        )


class MLConfig(BaseModel):
    """Machine Learning configuration."""

    enabled: bool = Field(default=True, description="Enable ML features")
    model_dir: str = Field(default="models", description="Directory for ML models")
    cache_dir: str = Field(default=".cache", description="Directory for caches")
    device: str = Field(default="cpu", description="Device: cpu or cuda")
    batch_size: int = Field(default=32, description="Batch size for inference")
    num_workers: int = Field(default=4, description="Number of data loading workers")

    @classmethod
    def from_env(cls):
        """Create from environment variables."""
        return cls(
            enabled=os.getenv("ML_ENABLED", "true").lower() == "true",
            model_dir=os.getenv("ML_MODEL_DIR", "models"),
            cache_dir=os.getenv("ML_CACHE_DIR", ".cache"),
            device=os.getenv("ML_DEVICE", "cpu"),
            batch_size=int(os.getenv("ML_BATCH_SIZE", "32")),
            num_workers=int(os.getenv("ML_NUM_WORKERS", "4")),
        )


class StorageConfig(BaseModel):
    """Storage configuration."""

    type: str = Field(default="sqlite", description="Storage type: sqlite, postgresql")
    path: str = Field(default="pokertool.db", description="Storage path or connection string")
    backup_dir: str = Field(default="backups", description="Backup directory")
    auto_backup: bool = Field(default=True, description="Enable automatic backups")
    backup_interval: int = Field(default=3600, description="Backup interval in seconds")
    encryption_key: Optional[str] = Field(default=None, description="Encryption key for sensitive data")

    @classmethod
    def from_env(cls):
        """Create from environment variables."""
        return cls(
            type=os.getenv("STORAGE_TYPE", "sqlite"),
            path=os.getenv("STORAGE_PATH", "pokertool.db"),
            backup_dir=os.getenv("STORAGE_BACKUP_DIR", "backups"),
            auto_backup=os.getenv("STORAGE_AUTO_BACKUP", "true").lower() == "true",
            backup_interval=int(os.getenv("STORAGE_BACKUP_INTERVAL", "3600")),
            encryption_key=os.getenv("STORAGE_ENCRYPTION_KEY"),
        )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format: json, text")
    file: Optional[str] = Field(default="pokertool.log", description="Log file path")
    max_bytes: int = Field(default=10485760, description="Max log file size in bytes (10MB)")
    backup_count: int = Field(default=5, description="Number of backup log files")
    console: bool = Field(default=True, description="Log to console")
    file_enabled: bool = Field(default=True, description="Log to file")

    @classmethod
    def from_env(cls):
        """Create from environment variables."""
        return cls(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "json"),
            file=os.getenv("LOG_FILE", "pokertool.log"),
            max_bytes=int(os.getenv("LOG_MAX_BYTES", "10485760")),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
            console=os.getenv("LOG_CONSOLE", "true").lower() == "true",
            file_enabled=os.getenv("LOG_FILE_ENABLED", "true").lower() == "true",
        )


class SecurityConfig(BaseModel):
    """Security configuration."""

    api_key_required: bool = Field(default=True, description="Require API key")
    jwt_secret: Optional[str] = Field(default=None, description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration: int = Field(default=3600, description="JWT expiration in seconds")
    cors_origins: str = Field(default="*", description="CORS origins (comma-separated)")
    ssl_enabled: bool = Field(default=False, description="Enable SSL/TLS")
    ssl_cert: Optional[str] = Field(default=None, description="SSL certificate file")
    ssl_key: Optional[str] = Field(default=None, description="SSL key file")

    @classmethod
    def from_env(cls):
        """Create from environment variables."""
        return cls(
            api_key_required=os.getenv("SECURITY_API_KEY_REQUIRED", "true").lower() == "true",
            jwt_secret=os.getenv("SECURITY_JWT_SECRET"),
            jwt_algorithm=os.getenv("SECURITY_JWT_ALGORITHM", "HS256"),
            jwt_expiration=int(os.getenv("SECURITY_JWT_EXPIRATION", "3600")),
            cors_origins=os.getenv("SECURITY_CORS_ORIGINS", "*"),
            ssl_enabled=os.getenv("SECURITY_SSL_ENABLED", "false").lower() == "true",
            ssl_cert=os.getenv("SECURITY_SSL_CERT"),
            ssl_key=os.getenv("SECURITY_SSL_KEY"),
        )


class AppConfig(BaseModel):
    """Main application configuration."""

    app_name: str = Field(default="PokerTool", description="Application name")
    version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=False, description="Debug mode")

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    ml: MLConfig = Field(default_factory=MLConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    @classmethod
    def from_env(cls):
        """Create configuration from environment variables."""
        return cls(
            app_name=os.getenv("APP_NAME", "PokerTool"),
            version=os.getenv("APP_VERSION", "1.0.0"),
            environment=os.getenv("APP_ENVIRONMENT", "development"),
            debug=os.getenv("APP_DEBUG", "false").lower() == "true",
            database=DatabaseConfig.from_env(),
            api=APIConfig.from_env(),
            ocr=OCRConfig.from_env(),
            ml=MLConfig.from_env(),
            storage=StorageConfig.from_env(),
            logging=LoggingConfig.from_env(),
            security=SecurityConfig.from_env(),
        )


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get the global configuration instance.

    Returns:
        AppConfig: The application configuration

    Raises:
        RuntimeError: If configuration initialization failed
    """
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config


def load_config(from_env: bool = True) -> AppConfig:
    """
    Load configuration.

    Args:
        from_env: Whether to load from environment variables

    Returns:
        AppConfig: The loaded configuration
    """
    global _config

    if from_env:
        _config = AppConfig.from_env()
    else:
        _config = AppConfig()

    return _config


def reset_config() -> None:
    """Reset the global configuration instance (useful for testing)."""
    global _config
    _config = None


if __name__ == "__main__":
    # Print current configuration
    config = get_config()
    print(config.model_dump_json(indent=2))
