"""Unique identifier generation and trace ID management.

This module provides functions for generating unique identifiers
and extracting trace IDs from OpenTelemetry context.
"""

import uuid

from opentelemetry import trace


def generate() -> str:
    """Generate a unique identifier using UUID4.

    Returns:
        A unique UUID string (e.g., "123e4567-e89b-12d3-a456-426614174000")

    Example:
        ```python
        request_id = generate()
        print(request_id)  # "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        ```
    """
    return str(uuid.uuid4())


def get_trace_id() -> str:
    """Get the current OpenTelemetry trace ID.

    Extracts the trace ID from the current OpenTelemetry span context.
    This is useful for correlating logs and requests across services.

    Returns:
        32-character hexadecimal trace ID string, or "0" * 32 if no active trace

    Example:
        ```python
        trace_id = get_trace_id()
        print(trace_id)  # "a1b2c3d4e5f67890abcdef1234567890"

        # Use in response headers
        response.headers["X-Trace-ID"] = trace_id
        ```

    Note:
        This requires OpenTelemetry to be properly configured and an active
        trace context to exist. Otherwise, it returns a zero trace ID.
    """
    return trace.format_trace_id(trace.get_current_span().get_span_context().trace_id)
