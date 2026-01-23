"""Test BaseModel."""

import pytest
from pydantic import ValidationError

from fastapi_bootstrap import BaseModel


def test_base_model_basic():
    """Test basic BaseModel functionality."""

    class TestModel(BaseModel):
        name: str
        age: int

    model = TestModel(name="John", age=30)
    assert model.name == "John"
    assert model.age == 30


def test_base_model_forbid_extra():
    """Test that extra fields are forbidden."""

    class TestModel(BaseModel):
        name: str

    with pytest.raises(ValidationError):
        TestModel(name="John", extra_field="value")  # type: ignore[call-arg]


def test_base_model_populate_by_name():
    """Test populate_by_name (camelCase support)."""
    from pydantic import Field

    class TestModel(BaseModel):
        user_name: str = Field(alias="userName")

    # Both should work
    model1 = TestModel(userName="John")
    assert model1.user_name == "John"

    model2 = TestModel(user_name="Jane")  # type: ignore[call-arg]
    assert model2.user_name == "Jane"


def test_base_model_validation():
    """Test type validation."""

    class TestModel(BaseModel):
        age: int
        active: bool

    with pytest.raises(ValidationError):
        TestModel(age="not a number", active=True)  # type: ignore[arg-type]
