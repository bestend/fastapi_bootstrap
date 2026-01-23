# Contributing to FastAPI Bootstrap

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setup with uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/bestend/fastapi_bootstrap.git
cd fastapi_bootstrap

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync --all-extras

# Install pre-commit hooks (optional but recommended)
uv run pre-commit install
```

### Setup with pip

```bash
git clone https://github.com/bestend/fastapi_bootstrap.git
cd fastapi_bootstrap

python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,auth]"
```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=fastapi_bootstrap --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_config.py -v

# Run specific test
uv run pytest tests/test_config.py::TestDocsSettings -v
```

### Code Quality

```bash
# Format code
uvx ruff format .

# Lint code
uvx ruff check --fix .

# Type check
uvx ty check .
```

### Pre-commit Checks

Before committing, ensure all checks pass:

```bash
uvx ruff format .
uvx ruff check --fix .
uvx ty check .
uv run pytest
```

## Project Structure

```
fastapi_bootstrap/
├── src/fastapi_bootstrap/     # Main package
│   ├── __init__.py           # Package exports
│   ├── base.py               # create_app() factory
│   ├── config.py             # BootstrapSettings and sub-configs
│   ├── auth.py               # OIDC authentication
│   ├── exception/            # Exception handling
│   ├── log/                  # Logging setup
│   ├── middleware/           # Middleware classes
│   ├── metrics.py            # Prometheus metrics
│   ├── response.py           # Response formatting
│   └── type/                 # Enhanced types
├── tests/                    # Test files
├── examples/                 # Example applications
└── docs/                     # Documentation
```

## Coding Standards

### Python Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Maximum line length: 100 characters (enforced by ruff)

### Docstrings

- Use Google-style docstrings for public APIs
- Keep docstrings concise and focused
- Code should be self-documenting where possible

```python
def create_app(
    routers: list[APIRouter],
    settings: BootstrapSettings | None = None,
) -> FastAPI:
    """Create a FastAPI application with preconfigured features.
    
    Args:
        routers: List of APIRouter instances to include
        settings: Configuration settings (uses defaults if None)
    
    Returns:
        Configured FastAPI application
    """
```

### Testing

- Write tests for all new functionality
- Follow TDD when possible (write tests first)
- Use pytest fixtures for common setup
- Aim for high coverage on new code

```python
def test_feature_name():
    """Test description."""
    # Arrange
    settings = BootstrapSettings(...)
    
    # Act
    result = some_function(settings)
    
    # Assert
    assert result == expected
```

## Making Changes

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring

### Commit Messages

Use conventional commit format:

```
type: short description

Longer description if needed.

- Bullet points for details
- Another point
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

### Pull Requests

1. Create a branch from `main`
2. Make your changes
3. Ensure all tests pass
4. Update documentation if needed
5. Create a pull request with clear description

## Adding New Features

### Adding a New Settings Class

1. Add the settings class in `config.py`:
```python
class MyNewSettings(BaseModel):
    """Description of settings."""
    
    enabled: bool = Field(default=True, description="Enable feature")
```

2. Add to `BootstrapSettings`:
```python
class BootstrapSettings(BaseModel):
    # ...
    my_new: MyNewSettings = Field(default_factory=MyNewSettings)
```

3. Add environment variable parsing in `from_env()` if needed

4. Write tests in `tests/test_config.py`

### Adding a New Middleware

1. Create middleware in `middleware/__init__.py`:
```python
class MyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Pre-processing
        response = await call_next(request)
        # Post-processing
        return response
```

2. Export in `__init__.py`

3. Write tests

4. Add documentation in `ADVANCED.md`

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions

Thank you for contributing!
