"""Enhanced Pydantic BaseModel with sensible defaults.

This module provides a BaseModel class with pre-configured settings
suitable for FastAPI applications.
"""

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseModel(PydanticBaseModel):
    """Enhanced Pydantic BaseModel with strict validation and field aliasing.

    This BaseModel is configured with:
    - `extra="forbid"`: Reject unknown fields in input data
    - `arbitrary_types_allowed=True`: Allow arbitrary Python types
    - `populate_by_name=True`: Accept both field names and aliases

    The populate_by_name setting is particularly useful for APIs that need
    to support both camelCase (JSON convention) and snake_case (Python convention).

    Example:
        ```python
        from pydantic import Field
        from fastapi_bootstrap import BaseModel

        class UserRequest(BaseModel):
            user_name: str = Field(alias="userName")
            email: str
            age: int = 0

        # Both work:
        user1 = UserRequest(userName="john", email="john@example.com")
        user2 = UserRequest(user_name="jane", email="jane@example.com")

        # This raises ValidationError (extra field):
        # user3 = UserRequest(userName="bob", email="bob@example.com", extra="value")
        ```
    """

    model_config = ConfigDict(
        extra="forbid",  # Reject unknown fields
        arbitrary_types_allowed=True,  # Allow custom Python types
        populate_by_name=True,  # Accept both field name and alias
    )
