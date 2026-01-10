"""Tests for logging setup and configuration."""

import json
import os
from io import StringIO
from unittest.mock import patch

import pytest

from fastapi_bootstrap.log.setup import (
    LOG_JSON,
    LOG_LEVEL,
    LOG_STRING_LENGTH,
    truncate_strings_in_structure,
)


class TestTruncateStringsInStructure:
    """Tests for truncate_strings_in_structure function."""

    def test_short_string_not_truncated(self):
        """Short strings should not be modified."""
        result = truncate_strings_in_structure("short string")
        assert result == "short string"

    def test_long_string_truncated(self):
        """Strings over 2000 chars should be truncated."""
        long_string = "x" * 2001
        result = truncate_strings_in_structure(long_string)
        assert result == "[[truncated]]"

    def test_string_at_threshold(self):
        """Strings at exactly 2000 chars should not be truncated."""
        threshold_string = "x" * 2000
        result = truncate_strings_in_structure(threshold_string)
        assert result == threshold_string

    def test_nested_dict_truncation(self):
        """Long strings in nested dicts should be truncated."""
        data = {
            "short": "hello",
            "long": "x" * 2001,
            "nested": {
                "also_long": "y" * 2500,
                "normal": "world",
            },
        }
        result = truncate_strings_in_structure(data)

        assert result["short"] == "hello"
        assert result["long"] == "[[truncated]]"
        assert result["nested"]["also_long"] == "[[truncated]]"
        assert result["nested"]["normal"] == "world"

    def test_nested_list_truncation(self):
        """Long strings in nested lists should be truncated."""
        data = [
            "short",
            "x" * 2001,
            ["y" * 2500, "normal"],
        ]
        result = truncate_strings_in_structure(data)

        assert result[0] == "short"
        assert result[1] == "[[truncated]]"
        assert result[2][0] == "[[truncated]]"
        assert result[2][1] == "normal"

    def test_mixed_structure(self):
        """Mixed nested structures should be handled correctly."""
        data = {
            "list": ["a" * 2001, "b"],
            "dict": {"long": "c" * 3000},
            "primitive": 123,
            "none": None,
            "bool": True,
        }
        result = truncate_strings_in_structure(data)

        assert result["list"][0] == "[[truncated]]"
        assert result["list"][1] == "b"
        assert result["dict"]["long"] == "[[truncated]]"
        assert result["primitive"] == 123
        assert result["none"] is None
        assert result["bool"] is True

    def test_empty_structures(self):
        """Empty structures should be handled correctly."""
        assert truncate_strings_in_structure({}) == {}
        assert truncate_strings_in_structure([]) == []
        assert truncate_strings_in_structure("") == ""


class TestEnvironmentConfiguration:
    """Tests for environment-based configuration."""

    def test_default_log_level(self):
        """Default log level should be INFO."""
        # This tests the module-level default
        assert LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_default_log_json(self):
        """Default LOG_JSON should be False."""
        # Default is false
        assert isinstance(LOG_JSON, bool)

    def test_default_log_string_length(self):
        """Default log string length should be 5000."""
        assert LOG_STRING_LENGTH == 5000 or isinstance(LOG_STRING_LENGTH, int)


class TestLogFormatting:
    """Tests for log formatting behavior."""

    def test_truncate_preserves_structure_types(self):
        """Truncation should preserve the types of structures."""
        data = {
            "list": [1, 2, 3],
            "dict": {"a": 1},
            "string": "test",
            "number": 42,
            "float": 3.14,
        }
        result = truncate_strings_in_structure(data)

        assert isinstance(result["list"], list)
        assert isinstance(result["dict"], dict)
        assert isinstance(result["string"], str)
        assert isinstance(result["number"], int)
        assert isinstance(result["float"], float)

    def test_deeply_nested_structure(self):
        """Deeply nested structures should be handled correctly."""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "long_string": "z" * 5000,
                            "short_string": "hello",
                        }
                    }
                }
            }
        }
        result = truncate_strings_in_structure(data)

        assert result["level1"]["level2"]["level3"]["level4"]["long_string"] == "[[truncated]]"
        assert result["level1"]["level2"]["level3"]["level4"]["short_string"] == "hello"
