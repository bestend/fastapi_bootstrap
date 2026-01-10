"""Tests for configuration module."""

import os
from unittest.mock import patch

import pytest

from fastapi_bootstrap.config import (
    BootstrapSettings,
    CORSSettings,
    GracefulShutdownSettings,
    HealthCheckSettings,
    LogFormat,
    LoggingSettings,
    MetricsSettings,
    RateLimitSettings,
    SecuritySettings,
    Stage,
    get_settings,
    mask_sensitive_data,
)


class TestLoggingSettings:
    """Tests for LoggingSettings."""

    def test_default_values(self):
        """Default logging settings should be sensible."""
        settings = LoggingSettings()
        assert settings.level == "INFO"
        assert settings.format == LogFormat.TEXT
        assert settings.string_max_length == 5000
        assert settings.truncation_threshold == 2000

    def test_level_validation(self):
        """Log level should be validated and normalized."""
        settings = LoggingSettings(level="debug")
        assert settings.level == "DEBUG"

        settings = LoggingSettings(level="WARNING")
        assert settings.level == "WARNING"

    def test_invalid_level_raises(self):
        """Invalid log level should raise ValueError."""
        with pytest.raises(ValueError):
            LoggingSettings(level="INVALID")


class TestCORSSettings:
    """Tests for CORSSettings."""

    def test_default_values(self):
        """Default CORS settings should be empty origins."""
        settings = CORSSettings()
        assert settings.origins == []
        assert settings.allow_credentials is True
        assert "GET" in settings.allow_methods

    def test_custom_origins(self):
        """Custom origins should be set correctly."""
        settings = CORSSettings(origins=["https://example.com", "https://api.example.com"])
        assert len(settings.origins) == 2
        assert "https://example.com" in settings.origins


class TestSecuritySettings:
    """Tests for SecuritySettings."""

    def test_default_sensitive_fields(self):
        """Default sensitive fields should include common patterns."""
        settings = SecuritySettings()
        assert "password" in settings.mask_sensitive_fields
        assert "token" in settings.mask_sensitive_fields
        assert "secret" in settings.mask_sensitive_fields
        assert "api_key" in settings.mask_sensitive_fields

    def test_security_header_defaults(self):
        """Security header defaults should be secure."""
        settings = SecuritySettings()
        assert settings.enable_security_headers is True
        assert settings.hsts_max_age == 31536000
        assert settings.x_frame_options == "DENY"


class TestBootstrapSettings:
    """Tests for main BootstrapSettings class."""

    def test_default_stage(self):
        """Default stage should be dev."""
        settings = BootstrapSettings()
        assert settings.stage == Stage.DEV

    def test_nested_settings(self):
        """Nested settings should be accessible."""
        settings = BootstrapSettings()
        assert isinstance(settings.logging, LoggingSettings)
        assert isinstance(settings.cors, CORSSettings)
        assert isinstance(settings.security, SecuritySettings)

    def test_from_env_basic(self):
        """from_env should load from environment variables."""
        with patch.dict(
            os.environ,
            {
                "STAGE": "prod",
                "LOG_LEVEL": "WARNING",
                "APP_TITLE": "Test API",
            },
            clear=False,
        ):
            # Clear cache
            get_settings.cache_clear()
            settings = BootstrapSettings.from_env()
            assert settings.stage == Stage.PROD
            assert settings.logging.level == "WARNING"
            assert settings.title == "Test API"

    def test_from_env_cors_origins(self):
        """from_env should parse CORS_ORIGINS correctly."""
        with patch.dict(
            os.environ,
            {
                "CORS_ORIGINS": "https://a.com,https://b.com, https://c.com",
            },
            clear=False,
        ):
            settings = BootstrapSettings.from_env()
            assert "https://a.com" in settings.cors.origins
            assert "https://b.com" in settings.cors.origins
            assert "https://c.com" in settings.cors.origins

    def test_get_cors_config_for_dev_stage(self):
        """Dev stage should have permissive CORS defaults."""
        settings = BootstrapSettings(stage=Stage.DEV)
        cors = settings.get_cors_config_for_stage()
        assert "*" in cors.origins
        assert "*" in cors.allow_methods

    def test_get_cors_config_for_prod_stage(self):
        """Prod stage should have restrictive CORS defaults."""
        settings = BootstrapSettings(stage=Stage.PROD)
        cors = settings.get_cors_config_for_stage()
        assert cors.origins == []  # Empty by default
        assert "*" not in cors.allow_methods

    def test_get_cors_config_with_explicit_origins(self):
        """Explicit origins should override stage defaults."""
        settings = BootstrapSettings(
            stage=Stage.DEV, cors=CORSSettings(origins=["https://custom.com"])
        )
        cors = settings.get_cors_config_for_stage()
        assert cors.origins == ["https://custom.com"]


class TestMaskSensitiveData:
    """Tests for mask_sensitive_data function."""

    def test_mask_password(self):
        """Password fields should be masked."""
        data = {"username": "john", "password": "secret123"}
        result = mask_sensitive_data(data)
        assert result["username"] == "john"
        assert result["password"] == "***MASKED***"

    def test_mask_nested_sensitive_data(self):
        """Sensitive fields in nested structures should be masked."""
        data = {
            "user": {
                "email": "john@example.com",
                "credentials": {
                    "api_key": "key123",
                    "secret": "shhh",
                },
            }
        }
        result = mask_sensitive_data(data)
        assert result["user"]["email"] == "john@example.com"
        assert result["user"]["credentials"]["api_key"] == "***MASKED***"
        assert result["user"]["credentials"]["secret"] == "***MASKED***"

    def test_mask_in_list(self):
        """Sensitive fields in lists should be masked."""
        data = [{"token": "abc123"}, {"token": "def456"}]
        result = mask_sensitive_data(data)
        assert result[0]["token"] == "***MASKED***"
        assert result[1]["token"] == "***MASKED***"

    def test_case_insensitive_masking(self):
        """Masking should be case-insensitive."""
        data = {"PASSWORD": "secret", "Token": "abc", "API_KEY": "key"}
        result = mask_sensitive_data(data)
        assert result["PASSWORD"] == "***MASKED***"
        assert result["Token"] == "***MASKED***"
        assert result["API_KEY"] == "***MASKED***"

    def test_custom_sensitive_fields(self):
        """Custom sensitive fields should be supported."""
        data = {"custom_secret": "value", "normal": "data"}
        result = mask_sensitive_data(data, sensitive_fields=["custom_secret"])
        assert result["custom_secret"] == "***MASKED***"
        assert result["normal"] == "data"

    def test_non_dict_data(self):
        """Non-dict data should pass through unchanged."""
        assert mask_sensitive_data("string") == "string"
        assert mask_sensitive_data(123) == 123
        assert mask_sensitive_data(None) is None
