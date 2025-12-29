"""OAuth2/OIDC authentication utilities for FastAPI.

This module provides easy integration with OAuth2/OIDC providers like Keycloak,
Auth0, Google, etc. It handles token validation, user info extraction, and
dependency injection for protected routes.
"""


import time
from collections.abc import Callable
from typing import Any

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import (
    HTTPBearer,
    OAuth2AuthorizationCodeBearer,
)
from jose import JWTError, jwt
from pydantic import BaseModel, Field

from fastapikit.log import get_logger

logger = get_logger()


class OIDCConfig(BaseModel):
    """OIDC provider configuration.

    Attributes:
        issuer: OIDC issuer URL (e.g., "https://keycloak.example.com/realms/myrealm")
        client_id: OAuth2 client ID
        client_secret: OAuth2 client secret (optional, for confidential clients)
        audience: Expected audience in JWT (defaults to client_id)
        algorithms: Allowed JWT algorithms (default: ["RS256"])
        verify_signature: Verify JWT signature (default: True, disable for dev only)
        verify_exp: Verify token expiration (default: True)
        leeway: Time leeway in seconds for exp/nbf validation (default: 0)

    Example:
        ```python
        # Keycloak
        config = OIDCConfig(
            issuer="https://keycloak.example.com/realms/myrealm",
            client_id="my-api-client"
        )

        # Auth0
        config = OIDCConfig(
            issuer="https://myapp.auth0.com",
            client_id="abc123",
            audience="https://api.myapp.com"
        )
        ```
    """

    issuer: str = Field(description="OIDC issuer URL")
    client_id: str = Field(description="OAuth2 client ID")
    client_secret: str | None = Field(default=None, description="Client secret (optional)")
    audience: str | None = Field(
        default=None,
        description="Expected audience. If None, audience validation is skipped. "
        "Some OIDC providers (like Keycloak) may not set audience claim.",
    )
    algorithms: list[str] = Field(default=["RS256"], description="Allowed JWT algorithms")
    verify_signature: bool = Field(default=True, description="Verify JWT signature")
    verify_exp: bool = Field(default=True, description="Verify token expiration")
    leeway: int = Field(default=0, description="Time leeway for exp/nbf validation (seconds)")

    # Remove model_post_init to allow audience=None


class TokenPayload(BaseModel):
    """Decoded JWT token payload.

    Attributes:
        sub: Subject (user ID)
        email: User email
        preferred_username: Preferred username
        name: Full name
        given_name: First name
        family_name: Last name
        exp: Expiration timestamp
        iat: Issued at timestamp
        roles: List of user roles
        groups: List of user groups
        raw: Raw token payload with all claims
    """

    sub: str = Field(description="Subject (user ID)")
    email: str | None = Field(default=None, description="User email")
    preferred_username: str | None = Field(default=None, description="Preferred username")
    name: str | None = Field(default=None, description="Full name")
    given_name: str | None = Field(default=None, description="First name")
    family_name: str | None = Field(default=None, description="Last name")
    exp: int | None = Field(default=None, description="Expiration timestamp")
    iat: int | None = Field(default=None, description="Issued at timestamp")
    roles: list[str] = Field(default_factory=list, description="User roles")
    groups: list[str] = Field(default_factory=list, description="User groups")
    raw: dict[str, Any] = Field(default_factory=dict, description="Raw token payload")

    @classmethod
    def from_jwt(cls, payload: dict[str, Any]) -> "TokenPayload":
        """Create TokenPayload from JWT payload.

        Args:
            payload: Decoded JWT payload dictionary

        Returns:
            TokenPayload instance with extracted claims
        """
        # Extract roles from various common locations
        roles = []
        if "realm_access" in payload and "roles" in payload["realm_access"]:
            roles.extend(payload["realm_access"]["roles"])
        if "resource_access" in payload:
            for client, data in payload["resource_access"].items():
                if "roles" in data:
                    roles.extend(data["roles"])
        if "roles" in payload:
            roles.extend(payload["roles"])

        # Extract groups
        groups = payload.get("groups", [])

        return cls(
            sub=payload.get("sub", ""),
            email=payload.get("email"),
            preferred_username=payload.get("preferred_username"),
            name=payload.get("name"),
            given_name=payload.get("given_name"),
            family_name=payload.get("family_name"),
            exp=payload.get("exp"),
            iat=payload.get("iat"),
            roles=roles,
            groups=groups,
            raw=payload,
        )


class OIDCAuth:
    """OAuth2/OIDC authentication handler.

    Handles JWT token validation, JWKS caching, and user info extraction.

    Attributes:
        config: OIDC configuration
        security: HTTPBearer security scheme
        oauth2_scheme: OAuth2 scheme for Swagger UI (optional)
    """

    config: OIDCConfig
    security: HTTPBearer
    oauth2_scheme: OAuth2AuthorizationCodeBearer | None

    def __init__(self, config: OIDCConfig, enable_swagger_ui: bool = True):
        """Initialize OIDC authentication handler.

        Args:
            config: OIDC configuration
            enable_swagger_ui: Enable OAuth2 flow in Swagger UI (default: True)
        """
        self.config = config
        self.enable_swagger_ui = enable_swagger_ui

        # For API calls (Bearer token validation)
        self.security = HTTPBearer()

        # For Swagger UI OAuth2 flow
        if enable_swagger_ui:
            # Get OIDC endpoints
            try:
                oidc_config = self._get_oidc_config()
                auth_url = oidc_config.get("authorization_endpoint")
                token_url = oidc_config.get("token_endpoint")
            except Exception as e:
                logger.warning(f"Failed to fetch OIDC config for Swagger UI: {e}")
                auth_url = None
                token_url = None

            # Only create OAuth2 scheme if we have valid URLs
            if auth_url and token_url and isinstance(auth_url, str) and isinstance(token_url, str):
                self.oauth2_scheme = OAuth2AuthorizationCodeBearer(
                    authorizationUrl=auth_url,
                    tokenUrl=token_url,
                    scopes={
                        "openid": "OpenID Connect",
                        "profile": "User profile",
                        "email": "Email address",
                    },
                    auto_error=False,  # Don't auto-error, we handle it manually
                )
            else:
                self.oauth2_scheme = None
        else:
            self.oauth2_scheme = None

        self._jwks_cache: dict[str, Any] | None = None
        self._jwks_cache_time: float = 0
        self._jwks_cache_ttl: int = 3600  # 1 hour
        self._oidc_config_cache: dict[str, Any] | None = None

    def _get_oidc_config(self) -> dict[str, Any]:
        """Fetch OIDC configuration from .well-known endpoint.

        Returns:
            OIDC configuration dictionary
        """
        # Return cached config if available
        if self._oidc_config_cache:
            return self._oidc_config_cache

        url = f"{self.config.issuer}/.well-known/openid-configuration"
        logger.info(f"Fetching OIDC configuration from {url}")

        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        self._oidc_config_cache = response.json()
        return self._oidc_config_cache

    def _get_jwks(self) -> dict[str, Any]:
        """Fetch JWKS (JSON Web Key Set) from provider.

        Returns:
            JWKS dictionary
        """
        # Check cache
        if self._jwks_cache and (time.time() - self._jwks_cache_time) < self._jwks_cache_ttl:
            return self._jwks_cache

        # Fetch fresh JWKS
        oidc_config = self._get_oidc_config()
        jwks_uri = oidc_config["jwks_uri"]

        logger.info(f"Fetching JWKS from {jwks_uri}")
        response = httpx.get(jwks_uri, timeout=10)
        response.raise_for_status()

        self._jwks_cache = response.json()
        self._jwks_cache_time = time.time()

        return self._jwks_cache

    def _get_signing_key(self, token: str) -> dict[str, Any]:
        """Get signing key for JWT token.

        Args:
            token: JWT token string

        Returns:
            Signing key dictionary

        Raises:
            HTTPException: If signing key not found
        """
        try:
            # Decode header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token header missing 'kid'",
                )

            # Find matching key in JWKS
            jwks = self._get_jwks()
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    return key

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Signing key with kid '{kid}' not found",
            )
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token header: {str(e)}",
            )

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify and decode JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Get signing key
            signing_key = self._get_signing_key(token)

            # Decode and verify token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=self.config.algorithms,
                audience=self.config.audience,
                issuer=self.config.issuer,
                options={
                    "verify_signature": self.config.verify_signature,
                    "verify_exp": self.config.verify_exp,
                    "verify_aud": self.config.audience is not None,
                    "leeway": self.config.leeway,
                },
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        except jwt.JWTClaimsError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token claims: {str(e)}",
            )
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
            )

    def get_current_user_dependency(
        self,
    ) -> Callable[..., Any]:
        """Create a dependency for getting the current user.

        This method returns a FastAPI dependency function that validates
        the JWT token and returns the user information.

        Returns:
            FastAPI dependency function

        Example:
            ```python
            @router.get("/me")
            async def me(user: TokenPayload = Depends(auth.get_current_user)):
                return {"email": user.email}
            ```
        """
        # Use oauth2_scheme if available (for Swagger UI integration)
        if self.oauth2_scheme:

            async def dependency(token: str = Depends(self.oauth2_scheme)) -> TokenPayload:  # type: ignore[misc]
                """Validate token and return user info."""
                payload = self.verify_token(token)
                return TokenPayload.from_jwt(payload)

            return dependency
        else:
            # Fall back to manual header parsing
            async def dependency(request: Request) -> TokenPayload:  # type: ignore[misc]
                """Validate token from Authorization header."""
                auth_header = request.headers.get("Authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Not authenticated",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                token = auth_header.replace("Bearer ", "")
                payload = self.verify_token(token)
                return TokenPayload.from_jwt(payload)

            return dependency

    # For backward compatibility
    @property
    def get_current_user(self):
        """Get the current user dependency.

        This property returns a dependency function for use with FastAPI's Depends().
        """
        return self.get_current_user_dependency()

    def require_roles(self, required_roles: list[str], require_all: bool = False):
        """Create a dependency that requires specific roles.

        Args:
            required_roles: List of required role names
            require_all: If True, user must have all roles. If False, any role is sufficient.

        Returns:
            FastAPI dependency function

        Example:
            ```python
            # User needs admin OR moderator role
            @router.delete("/posts/{id}")
            async def delete_post(
                user: TokenPayload = Depends(auth.require_roles(["admin", "moderator"]))
            ):
                return {"status": "deleted"}

            # User needs BOTH admin AND superuser role
            @router.post("/system/restart")
            async def restart_system(
                user: TokenPayload = Depends(auth.require_roles(["admin", "superuser"], require_all=True))
            ):
                return {"status": "restarting"}
            ```
        """

        async def check_roles(
            user: TokenPayload = Depends(self.get_current_user),
        ) -> TokenPayload:
            user_roles = set(user.roles)
            required = set(required_roles)

            if require_all:
                # User must have all required roles
                if not required.issubset(user_roles):
                    missing = required - user_roles
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Missing required roles: {', '.join(missing)}",
                    )
            else:
                # User must have at least one required role
                if not required.intersection(user_roles):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Missing required roles. Need one of: {', '.join(required_roles)}",
                    )

            return user

        return check_roles

    def require_groups(self, required_groups: list[str], require_all: bool = False):
        """Create a dependency that requires specific groups.

        Args:
            required_groups: List of required group names
            require_all: If True, user must be in all groups. If False, any group is sufficient.

        Returns:
            FastAPI dependency function

        Example:
            ```python
            @router.get("/department/engineering")
            async def engineering_data(
                user: TokenPayload = Depends(auth.require_groups(["/engineering"]))
            ):
                return {"department": "engineering"}
            ```
        """

        async def check_groups(
            user: TokenPayload = Depends(self.get_current_user),
        ) -> TokenPayload:
            user_groups = set(user.groups)
            required = set(required_groups)

            if require_all:
                if not required.issubset(user_groups):
                    missing = required - user_groups
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Missing required groups: {', '.join(missing)}",
                    )
            else:
                if not required.intersection(user_groups):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Missing required groups. Need one of: {', '.join(required_groups)}",
                    )

            return user

        return check_groups

    def optional_auth(self):
        """Create a dependency for optional authentication.

        Returns user if token is provided and valid, None otherwise.

        Returns:
            FastAPI dependency function

        Example:
            ```python
            @router.get("/posts")
            async def list_posts(
                user: TokenPayload | None = Depends(auth.optional_auth())
            ):
                if user:
                    # Return personalized posts
                    return get_user_posts(user.sub)
                else:
                    # Return public posts
                    return get_public_posts()
            ```
        """

        async def get_optional_user(request: Request) -> TokenPayload | None:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None

            token = auth_header.replace("Bearer ", "")
            try:
                payload = self.verify_token(token)
                return TokenPayload.from_jwt(payload)
            except HTTPException:
                return None

        return get_optional_user
