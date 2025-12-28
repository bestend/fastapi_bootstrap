"""Utility functions for common tasks.

This module provides various helper functions used throughout the application.
"""

import time
from functools import wraps


def str2bool(v: str) -> bool:
    """Convert string to boolean value.

    Accepts various string representations of boolean values.

    Args:
        v: String value to convert

    Returns:
        Boolean value

    Raises:
        NotImplementedError: If the string is not a recognized boolean value

    Examples:
        >>> str2bool("yes")
        True
        >>> str2bool("no")
        False
        >>> str2bool("1")
        True
        >>> str2bool("0")
        False
    """
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise NotImplementedError(f"Cannot convert '{v}' to boolean")


def timeit(prefix: str = ""):
    """Decorator to measure and log function execution time.

    Args:
        prefix: Optional prefix for the log message. If empty, uses function name.

    Returns:
        Decorator function

    Example:
        ```python
        @timeit(prefix="Database query")
        def fetch_users():
            # ... database operation
            return users

        # Logs: "Database query time elapsed 0.123 sec"
        ```
    """
    from fastapi_kit.log import get_logger

    logger = get_logger()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time

            # Use custom prefix or function name
            module_name = prefix or f"{func.__name__}, "

            logger.info(f"{module_name}time elapsed {elapsed_time:.3f} sec")
            return result

        return wrapper

    return decorator
