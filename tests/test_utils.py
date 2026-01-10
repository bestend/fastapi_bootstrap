"""Tests for utility functions."""

import uuid

import pytest

from fastapi_bootstrap.util.etc import str2bool, timeit
from fastapi_bootstrap.util.identifier import generate, get_trace_id


class TestStr2Bool:
    """Tests for str2bool function."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("yes", True),
            ("YES", True),
            ("Yes", True),
            ("true", True),
            ("TRUE", True),
            ("True", True),
            ("t", True),
            ("T", True),
            ("y", True),
            ("Y", True),
            ("1", True),
        ],
    )
    def test_truthy_values(self, value: str, expected: bool):
        """Truthy string values should return True."""
        assert str2bool(value) == expected

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("no", False),
            ("NO", False),
            ("No", False),
            ("false", False),
            ("FALSE", False),
            ("False", False),
            ("f", False),
            ("F", False),
            ("n", False),
            ("N", False),
            ("0", False),
        ],
    )
    def test_falsy_values(self, value: str, expected: bool):
        """Falsy string values should return False."""
        assert str2bool(value) == expected

    def test_invalid_value_raises(self):
        """Invalid values should raise NotImplementedError."""
        with pytest.raises(NotImplementedError):
            str2bool("maybe")

        with pytest.raises(NotImplementedError):
            str2bool("invalid")

        with pytest.raises(NotImplementedError):
            str2bool("")


class TestTimeitDecorator:
    """Tests for timeit decorator."""

    def test_timeit_returns_function_result(self):
        """Timeit decorator should return the function's result."""

        @timeit()
        def add(a, b):
            return a + b

        result = add(2, 3)
        assert result == 5

    def test_timeit_with_prefix(self):
        """Timeit with prefix should work correctly."""

        @timeit(prefix="test_function")
        def multiply(a, b):
            return a * b

        result = multiply(3, 4)
        assert result == 12

    def test_timeit_preserves_function_name(self):
        """Timeit should preserve the original function name."""

        @timeit()
        def my_function():
            return "hello"

        # Note: Due to wraps, __name__ should be preserved
        assert my_function.__name__ == "my_function"


class TestGenerate:
    """Tests for generate UUID function."""

    def test_generate_returns_string(self):
        """Generate should return a string."""
        result = generate()
        assert isinstance(result, str)

    def test_generate_returns_valid_uuid(self):
        """Generate should return a valid UUID string."""
        result = generate()
        # Should not raise an exception
        parsed = uuid.UUID(result)
        assert str(parsed) == result

    def test_generate_returns_unique_values(self):
        """Generate should return unique values on each call."""
        results = [generate() for _ in range(100)]
        assert len(set(results)) == 100

    def test_generate_uuid4_format(self):
        """Generate should return UUID4 format."""
        result = generate()
        parsed = uuid.UUID(result)
        # UUID4 has version 4
        assert parsed.version == 4


class TestGetTraceId:
    """Tests for get_trace_id function."""

    def test_get_trace_id_returns_string(self):
        """Get trace ID should return a string."""
        result = get_trace_id()
        assert isinstance(result, str)

    def test_get_trace_id_returns_32_chars(self):
        """Get trace ID should return a 32-character string."""
        result = get_trace_id()
        assert len(result) == 32

    def test_get_trace_id_is_hexadecimal(self):
        """Get trace ID should return a hexadecimal string."""
        result = get_trace_id()
        # Should only contain hex characters
        assert all(c in "0123456789abcdef" for c in result)

    def test_get_trace_id_without_active_span(self):
        """Without active span, should return zero trace ID."""
        result = get_trace_id()
        # Without OpenTelemetry context, returns zeros
        assert result == "0" * 32
