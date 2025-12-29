"""fastapi_bootstrap.log

로깅 관련 유틸을 제공합니다.

주의: import 시점에 loguru Handler 동작을 패치하는 등 부수효과가 있습니다.
"""

from .loguru_helper import (
    InterceptHandler,
    get_logger,
    intercept_standard_logging,
    setup_logging,
    truncate_strings_in_structure,
)

__all__ = [
    "InterceptHandler",
    "get_logger",
    "intercept_standard_logging",
    "setup_logging",
    "truncate_strings_in_structure",
]
