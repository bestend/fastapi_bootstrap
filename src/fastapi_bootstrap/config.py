"""Configuration management for FastAPI Bootstrap.

This module provides centralized configuration using Pydantic Settings,
supporting environment variables, .env files, and programmatic configuration.

Example:
    ```python
    from fastapi_bootstrap.config import BootstrapSettings

    # Load from environment variables
    settings = BootstrapSettings()

    # Or override programmatically
    settings = BootstrapSettings(
        stage="prod",
        log_level="WARNING",
        cors_origins=["https://myapp.com"]
    )
    ```
"""

import os
from enum import Enum
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class Stage(str, Enum):
    """Application environment stage."""

    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class LogFormat(str, Enum):
    """Log output format."""

    JSON = "json"
    TEXT = "text"


class LoggingSettings(BaseModel):
    """Logging configuration settings."""

    level: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    format: LogFormat = Field(
        default=LogFormat.TEXT,
        description="Log output format (json or text)",
    )
    json_output: bool = Field(
        default=False,
        description="Enable JSON log output (deprecated, use format instead)",
    )
    string_max_length: int = Field(
        default=5000,
        ge=100,
        le=100000,
        description="Maximum length for logged strings before truncation",
    )
    truncation_threshold: int = Field(
        default=2000,
        ge=100,
        le=50000,
        description="Threshold for truncating strings in nested structures",
    )
    traceback_limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum traceback depth to show in logs",
    )

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate and normalize log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        normalized = v.upper()
        if normalized not in valid_levels:
            raise ValueError(
                f"Invalid log level: '{v}' (normalized: '{normalized}'). "
                f"Must be one of {sorted(valid_levels)}"
            )
        return normalized

    @model_validator(mode="after")
    def validate_format_consistency(self) -> "LoggingSettings":
        """Warn if json_output conflicts with format setting."""
        import warnings

        if self.json_output and self.format == LogFormat.TEXT:
            warnings.warn(
                "LoggingSettings has json_output=True but format=TEXT. "
                "The 'json_output' field is deprecated; use format=LogFormat.JSON instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        return self


class CORSSettings(BaseModel):
    """CORS (Cross-Origin Resource Sharing) configuration."""

    origins: list[str] = Field(
        default_factory=list,
        description="Allowed origins. Empty list means no origins allowed.",
    )
    allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests",
    )
    allow_methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        description="Allowed HTTP methods",
    )
    allow_headers: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed HTTP headers",
    )
    expose_headers: list[str] = Field(
        default_factory=lambda: ["X-Request-ID", "X-Trace-ID"],
        description="Headers exposed to the browser",
    )
    max_age: int = Field(
        default=600,
        ge=0,
        le=86400,
        description="Max age for CORS preflight cache (seconds)",
    )


class SecuritySettings(BaseModel):
    """Security-related configuration."""

    # Security Headers
    enable_security_headers: bool = Field(
        default=True,
        description="Enable security headers middleware",
    )
    hsts_max_age: int = Field(
        default=31536000,  # 1 year
        ge=0,
        description="HSTS max-age in seconds (0 to disable)",
    )
    content_security_policy: str | None = Field(
        default="default-src 'self'",
        description="Content-Security-Policy header value",
    )
    x_frame_options: str = Field(
        default="DENY",
        description="X-Frame-Options header value",
    )
    x_content_type_options: str = Field(
        default="nosniff",
        description="X-Content-Type-Options header value",
    )

    # Request limits
    max_request_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        ge=1024,
        description="Maximum request body size in bytes",
    )

    # Sensitive data masking
    mask_sensitive_fields: list[str] = Field(
        default_factory=lambda: [
            "password",
            "passwd",
            "secret",
            "token",
            "api_key",
            "apikey",
            "authorization",
            "auth",
            "credential",
            "private_key",
            "access_token",
            "refresh_token",
        ],
        description="Field names to mask in logs",
    )


class RateLimitSettings(BaseModel):
    """Rate limiting configuration."""

    enabled: bool = Field(
        default=False,
        description="Enable rate limiting",
    )
    requests_per_minute: int = Field(
        default=60,
        ge=1,
        description="Maximum requests per minute per client",
    )
    burst_size: int = Field(
        default=10,
        ge=1,
        description="Allowed burst size above the limit",
    )


class MetricsSettings(BaseModel):
    """Metrics and monitoring configuration."""

    enabled: bool = Field(
        default=False,
        description="Enable metrics endpoint",
    )
    endpoint: str = Field(
        default="/metrics",
        description="Metrics endpoint path",
    )
    include_in_schema: bool = Field(
        default=False,
        description="Include metrics endpoint in OpenAPI schema",
    )


class HealthCheckSettings(BaseModel):
    """Health check configuration."""

    endpoint: str = Field(
        default="/healthz",
        description="Health check endpoint path",
    )
    include_in_schema: bool = Field(
        default=False,
        description="Include health endpoint in OpenAPI schema",
    )


class GracefulShutdownSettings(BaseModel):
    """Graceful shutdown configuration."""

    timeout: int = Field(
        default=10,
        ge=0,
        le=300,
        description="Seconds to wait for in-flight requests during shutdown",
    )


class BootstrapSettings(BaseModel):
    """Main configuration class for FastAPI Bootstrap.

    This class aggregates all configuration settings and can be loaded
    from environment variables or configured programmatically.

    Environment Variables:
        - STAGE: Application stage (dev, staging, prod)
        - LOG_LEVEL: Logging level
        - LOG_JSON: Enable JSON logging ("true" or "false")
        - LOG_STRING_LENGTH: Max string length in logs
        - CORS_ORIGINS: Comma-separated list of allowed origins
        - RATE_LIMIT_ENABLED: Enable rate limiting
        - RATE_LIMIT_RPM: Requests per minute

    Example:
        ```python
        # Load from environment
        settings = BootstrapSettings()

        # Override specific values
        settings = BootstrapSettings(
            stage=Stage.PROD,
            logging=LoggingSettings(level="WARNING"),
            cors=CORSSettings(origins=["https://myapp.com"]),
        )
        ```
    """

    stage: Stage = Field(
        default=Stage.DEV,
        description="Application environment stage",
    )

    # Sub-configurations
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    metrics: MetricsSettings = Field(default_factory=MetricsSettings)
    health_check: HealthCheckSettings = Field(default_factory=HealthCheckSettings)
    graceful_shutdown: GracefulShutdownSettings = Field(default_factory=GracefulShutdownSettings)

    # Application metadata
    title: str = Field(default="FastAPI Application", description="API title")
    version: str = Field(default="0.1.0", description="API version")
    description: str = Field(default="", description="API description")

    model_config = {"use_enum_values": True}

    @classmethod
    def from_env(cls) -> "BootstrapSettings":
        """Load settings from environment variables.

        Returns:
            BootstrapSettings instance configured from environment

        Raises:
            ValueError: If environment variable cannot be parsed to expected type

        Example:
            ```python
            # Set environment variables
            # STAGE=prod
            # LOG_LEVEL=WARNING
            # CORS_ORIGINS=https://myapp.com,https://api.myapp.com

            settings = BootstrapSettings.from_env()
            ```
        """

        def parse_int_env(name: str, default: str) -> int:
            """Parse integer from environment variable with error handling."""
            value = os.getenv(name, default)
            try:
                return int(value)
            except ValueError as e:
                raise ValueError(
                    f"Environment variable {name} must be an integer, got: '{value}'"
                ) from e

        # Parse stage
        stage_str = os.getenv("STAGE", "dev").lower()
        stage = Stage(stage_str) if stage_str in [s.value for s in Stage] else Stage.DEV

        # Parse logging settings
        log_json = os.getenv("LOG_JSON", "false").lower() in ("true", "1", "yes")
        logging_settings = LoggingSettings(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=LogFormat.JSON if log_json else LogFormat.TEXT,
            json_output=log_json,
            string_max_length=parse_int_env("LOG_STRING_LENGTH", "5000"),
            truncation_threshold=parse_int_env("LOG_TRUNCATION_THRESHOLD", "2000"),
            traceback_limit=parse_int_env("TRACEBACKLIMIT", "10"),
        )

        # Parse CORS settings
        cors_origins_str = os.getenv("CORS_ORIGINS", "")
        cors_origins = [o.strip() for o in cors_origins_str.split(",") if o.strip()]
        allow_credentials = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() in (
            "true",
            "1",
            "yes",
        )

        # Validate CORS configuration - browsers reject credentials with wildcard
        if allow_credentials and "*" in cors_origins:
            raise ValueError(
                "Invalid CORS configuration: allow_credentials=True cannot be used "
                'with origins containing "*". Per the CORS specification, browsers '
                "will reject this combination. Configure explicit origins instead, "
                'e.g. CORS_ORIGINS="https://example.com,https://api.example.com"'
            )

        cors_settings = CORSSettings(
            origins=cors_origins,
            allow_credentials=allow_credentials,
        )

        # Parse rate limit settings
        rate_limit_settings = RateLimitSettings(
            enabled=os.getenv("RATE_LIMIT_ENABLED", "false").lower() in ("true", "1", "yes"),
            requests_per_minute=parse_int_env("RATE_LIMIT_RPM", "60"),
        )

        # Parse metrics settings
        metrics_settings = MetricsSettings(
            enabled=os.getenv("METRICS_ENABLED", "false").lower() in ("true", "1", "yes"),
            endpoint=os.getenv("METRICS_ENDPOINT", "/metrics"),
        )

        # Parse graceful shutdown
        graceful_settings = GracefulShutdownSettings(
            timeout=parse_int_env("GRACEFUL_SHUTDOWN_TIMEOUT", "10"),
        )

        return cls(
            stage=stage,
            logging=logging_settings,
            cors=cors_settings,
            rate_limit=rate_limit_settings,
            metrics=metrics_settings,
            graceful_shutdown=graceful_settings,
            title=os.getenv("APP_TITLE", "FastAPI Application"),
            version=os.getenv("APP_VERSION", "0.1.0"),
            description=os.getenv("APP_DESCRIPTION", ""),
        )

    def get_cors_config_for_stage(self) -> CORSSettings:
        """Get CORS configuration adjusted for the current stage.

        Returns:
            CORSSettings with stage-appropriate defaults applied
        """
        # If origins are explicitly set, use them
        if self.cors.origins:
            return self.cors

        # Apply stage-specific defaults
        if self.stage == Stage.DEV:
            return CORSSettings(
                origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
                allow_credentials=True,
            )
        elif self.stage == Stage.STAGING:
            return CORSSettings(
                origins=self.cors.origins or [],
                allow_methods=self.cors.allow_methods,
                allow_headers=self.cors.allow_headers,
                allow_credentials=True,
            )
        else:  # PROD
            return CORSSettings(
                origins=self.cors.origins,  # Must be explicitly set
                allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
                allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
                allow_credentials=True,
            )


@lru_cache()
def get_settings() -> BootstrapSettings:
    """Get cached settings instance.

    Returns:
        Cached BootstrapSettings instance loaded from environment

    Example:
        ```python
        from fastapi_bootstrap.config import get_settings

        settings = get_settings()
        print(settings.stage)  # "dev"
        ```
    """
    return BootstrapSettings.from_env()


def mask_sensitive_data(data: Any, sensitive_fields: list[str] | None = None) -> Any:
    """Mask sensitive fields in a data structure.

    Recursively traverses dictionaries and lists to mask values of
    fields that match sensitive field names.

    Args:
        data: Data structure to mask (dict, list, or primitive)
        sensitive_fields: List of field names to mask. If None, loads from
            get_settings().security.mask_sensitive_fields (cached via @lru_cache).

    Note:
        When sensitive_fields is None, this function calls get_settings() which
        requires BootstrapSettings to be loadable from environment. For standalone
        usage without environment configuration, provide explicit sensitive_fields.

    Returns:
        Data structure with sensitive values replaced with "***MASKED***"

    Example:
        ```python
        data = {"username": "john", "password": "secret123"}
        masked = mask_sensitive_data(data)
        # {"username": "john", "password": "***MASKED***"}
        ```
    """
    if sensitive_fields is None:
        sensitive_fields = get_settings().security.mask_sensitive_fields

    sensitive_set = {f.lower() for f in sensitive_fields}

    def _mask(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                k: "***MASKED***" if k.lower() in sensitive_set else _mask(v)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [_mask(item) for item in obj]
        else:
            return obj

    return _mask(data)
