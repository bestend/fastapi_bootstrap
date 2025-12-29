"""Test OIDC authentication."""

from unittest.mock import patch

import pytest
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from fastapi_bootstrap import create_app

# Skip if auth dependencies not installed
pytest.importorskip("jose")

from fastapi_bootstrap.auth import OIDCAuth, OIDCConfig, TokenPayload


@pytest.fixture
def oidc_config():
    """OIDC configuration for testing."""
    return OIDCConfig(
        issuer="https://keycloak.example.com/realms/test",
        client_id="test-client",
        verify_signature=False,  # Skip signature verification in tests
    )


@pytest.fixture
def oidc_auth(oidc_config):
    """OIDC auth instance."""
    return OIDCAuth(oidc_config)


@pytest.fixture
def mock_jwt_payload():
    """Sample JWT payload."""
    return {
        "sub": "user-123",
        "email": "user@example.com",
        "preferred_username": "testuser",
        "name": "Test User",
        "exp": 9999999999,  # Far future
        "iat": 1234567890,
        "realm_access": {"roles": ["user", "admin"]},
        "groups": ["/engineering", "/developers"],
    }


def test_oidc_config_default_audience():
    """Test that audience defaults to None (no validation)."""
    config = OIDCConfig(issuer="https://example.com", client_id="my-client")
    assert config.audience is None  # None means no audience validation


def test_oidc_config_custom_audience():
    """Test custom audience."""
    config = OIDCConfig(
        issuer="https://example.com",
        client_id="my-client",
        audience="https://api.example.com",
    )
    assert config.audience == "https://api.example.com"


def test_token_payload_from_jwt(mock_jwt_payload):
    """Test TokenPayload creation from JWT."""
    payload = TokenPayload.from_jwt(mock_jwt_payload)

    assert payload.sub == "user-123"
    assert payload.email == "user@example.com"
    assert payload.preferred_username == "testuser"
    assert payload.name == "Test User"
    assert "user" in payload.roles
    assert "admin" in payload.roles
    assert "/engineering" in payload.groups


def test_token_payload_roles_extraction():
    """Test role extraction from various locations."""
    # Realm roles
    payload1 = TokenPayload.from_jwt({"sub": "1", "realm_access": {"roles": ["role1", "role2"]}})
    assert "role1" in payload1.roles
    assert "role2" in payload1.roles

    # Resource roles
    payload2 = TokenPayload.from_jwt(
        {
            "sub": "2",
            "resource_access": {
                "client1": {"roles": ["role3"]},
                "client2": {"roles": ["role4"]},
            },
        }
    )
    assert "role3" in payload2.roles
    assert "role4" in payload2.roles

    # Direct roles
    payload3 = TokenPayload.from_jwt({"sub": "3", "roles": ["role5"]})
    assert "role5" in payload3.roles


@patch("fastapi_bootstrap.auth.jwt.decode")
def test_verify_token_success(mock_decode, oidc_auth, mock_jwt_payload):
    """Test successful token verification."""
    mock_decode.return_value = mock_jwt_payload

    with patch.object(oidc_auth, "_get_signing_key", return_value={}):
        payload = oidc_auth.verify_token("fake-token")

    assert payload == mock_jwt_payload


@patch("fastapi_bootstrap.auth.jwt.decode")
def test_verify_token_expired(mock_decode, oidc_auth):
    """Test expired token handling."""
    from jose import jwt as jose_jwt

    mock_decode.side_effect = jose_jwt.ExpiredSignatureError()

    with patch.object(oidc_auth, "_get_signing_key", return_value={}):
        with pytest.raises(Exception) as exc_info:
            oidc_auth.verify_token("expired-token")

    assert exc_info.value.status_code == 401
    assert "expired" in str(exc_info.value.detail).lower()


def test_protected_route_without_token(oidc_auth):
    """Test accessing protected route without token."""
    router = APIRouter()

    @router.get("/protected")
    async def protected(user: TokenPayload = Depends(oidc_auth.get_current_user)):
        return {"user": user.email}

    app = create_app([router], stage="dev")
    client = TestClient(app)

    response = client.get("/protected")
    assert response.status_code == 401  # HTTPBearer returns 401 for missing auth


@patch("fastapi_bootstrap.auth.jwt.decode")
def test_protected_route_with_valid_token(mock_decode, oidc_auth, mock_jwt_payload):
    """Test accessing protected route with valid token."""
    mock_decode.return_value = mock_jwt_payload

    router = APIRouter()

    @router.get("/protected")
    async def protected(user: TokenPayload = Depends(oidc_auth.get_current_user)):
        return {"user": user.email, "roles": user.roles}

    app = create_app([router], stage="dev")
    client = TestClient(app)

    with patch.object(oidc_auth, "_get_signing_key", return_value={}):
        response = client.get("/protected", headers={"Authorization": "Bearer fake-token"})

    assert response.status_code == 200
    data = response.json()
    assert data["user"] == "user@example.com"
    assert "admin" in data["roles"]


@patch("fastapi_bootstrap.auth.jwt.decode")
def test_require_roles_success(mock_decode, oidc_auth, mock_jwt_payload):
    """Test role requirement - user has required role."""
    mock_decode.return_value = mock_jwt_payload

    router = APIRouter()

    @router.get("/admin")
    async def admin_only(user: TokenPayload = Depends(oidc_auth.require_roles(["admin"]))):
        return {"message": "Admin access granted"}

    app = create_app([router], stage="dev")
    client = TestClient(app)

    with patch.object(oidc_auth, "_get_signing_key", return_value={}):
        response = client.get("/admin", headers={"Authorization": "Bearer fake-token"})

    assert response.status_code == 200


@patch("fastapi_bootstrap.auth.jwt.decode")
def test_require_roles_forbidden(mock_decode, oidc_auth, mock_jwt_payload):
    """Test role requirement - user missing required role."""
    mock_decode.return_value = mock_jwt_payload

    router = APIRouter()

    @router.get("/superadmin")
    async def superadmin_only(
        user: TokenPayload = Depends(oidc_auth.require_roles(["superadmin"])),
    ):
        return {"message": "Superadmin access"}

    app = create_app([router], stage="dev")
    client = TestClient(app)

    with patch.object(oidc_auth, "_get_signing_key", return_value={}):
        response = client.get("/superadmin", headers={"Authorization": "Bearer fake-token"})

    assert response.status_code == 403
    # Exception handler converts HTTPException detail to msg
    response_data = response.json()
    assert "msg" in response_data or "detail" in response_data


@patch("fastapi_bootstrap.auth.jwt.decode")
def test_require_all_roles(mock_decode, oidc_auth):
    """Test requiring all roles."""
    mock_decode.return_value = {
        "sub": "1",
        "realm_access": {"roles": ["admin"]},
    }

    router = APIRouter()

    @router.get("/restricted")
    async def restricted(
        user: TokenPayload = Depends(
            oidc_auth.require_roles(["admin", "superuser"], require_all=True)
        ),
    ):
        return {"message": "Access granted"}

    app = create_app([router], stage="dev")
    client = TestClient(app)

    with patch.object(oidc_auth, "_get_signing_key", return_value={}):
        response = client.get("/restricted", headers={"Authorization": "Bearer fake-token"})

    # User has admin but not superuser
    assert response.status_code == 403


@patch("fastapi_bootstrap.auth.jwt.decode")
def test_require_groups(mock_decode, oidc_auth, mock_jwt_payload):
    """Test group requirement."""
    mock_decode.return_value = mock_jwt_payload

    router = APIRouter()

    @router.get("/engineering")
    async def engineering_only(
        user: TokenPayload = Depends(oidc_auth.require_groups(["/engineering"])),
    ):
        return {"department": "engineering"}

    app = create_app([router], stage="dev")
    client = TestClient(app)

    with patch.object(oidc_auth, "_get_signing_key", return_value={}):
        response = client.get("/engineering", headers={"Authorization": "Bearer fake-token"})

    assert response.status_code == 200


@patch("fastapi_bootstrap.auth.jwt.decode")
def test_optional_auth_with_token(mock_decode, oidc_auth, mock_jwt_payload):
    """Test optional auth with valid token."""
    mock_decode.return_value = mock_jwt_payload

    router = APIRouter()

    @router.get("/posts")
    async def list_posts(user: TokenPayload | None = Depends(oidc_auth.optional_auth())):
        if user:
            return {"personalized": True, "user": user.email}
        return {"personalized": False}

    app = create_app([router], stage="dev")
    client = TestClient(app)

    with patch.object(oidc_auth, "_get_signing_key", return_value={}):
        response = client.get("/posts", headers={"Authorization": "Bearer fake-token"})

    assert response.status_code == 200
    data = response.json()
    assert data["personalized"] is True
    assert data["user"] == "user@example.com"


def test_optional_auth_without_token(oidc_auth):
    """Test optional auth without token."""
    router = APIRouter()

    @router.get("/posts")
    async def list_posts(user: TokenPayload | None = Depends(oidc_auth.optional_auth())):
        if user:
            return {"personalized": True}
        return {"personalized": False}

    app = create_app([router], stage="dev")
    client = TestClient(app)

    response = client.get("/posts")

    assert response.status_code == 200
    data = response.json()
    assert data["personalized"] is False
