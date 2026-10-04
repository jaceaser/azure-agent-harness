from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import jwt

from azure_agent_harness.auth.principal import Principal
from azure_agent_harness.config import Settings


class AuthenticationError(Exception):
    pass


class EntraTokenValidator:
    def __init__(
        self,
        *,
        tenant_id: str,
        audiences: Iterable[str],
        allowed_tenant_ids: Iterable[str] | None = None,
        jwks_client: Any | None = None,
        leeway_seconds: int = 60,
    ) -> None:
        self.tenant_id = tenant_id
        self.audiences = tuple(audience for audience in audiences if audience)
        self.allowed_tenant_ids = tuple(allowed_tenant_ids or (tenant_id,))
        self.jwks_client = jwks_client or jwt.PyJWKClient(
            f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys",
            cache_keys=True,
        )
        self.leeway_seconds = leeway_seconds

    @classmethod
    def from_settings(
        cls,
        settings: Settings,
        *,
        jwks_client: Any | None = None,
    ) -> EntraTokenValidator:
        return cls(
            tenant_id=settings.entra_tenant_id,
            audiences=settings.entra_audiences,
            allowed_tenant_ids=settings.entra_allowed_tenants,
            jwks_client=jwks_client,
        )

    def validate(self, token: str) -> Principal:
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=self.audiences,
                leeway=self.leeway_seconds,
                options={"require": ["exp", "iss", "aud", "tid"]},
            )
            self._validate_claims(claims)
            return self._principal_from_claims(claims)
        except Exception as exc:
            if isinstance(exc, AuthenticationError):
                raise
            raise AuthenticationError("Invalid Entra access token") from exc

    def _validate_claims(self, claims: dict[str, Any]) -> None:
        tenant_id = claims.get("tid")
        if not isinstance(tenant_id, str):
            raise AuthenticationError("Invalid Entra access token")
        if tenant_id not in self.allowed_tenant_ids:
            raise AuthenticationError("Invalid Entra access token")

        issuer = claims.get("iss")
        valid_issuers = {
            f"https://login.microsoftonline.com/{tenant_id}/v2.0",
            f"https://sts.windows.net/{tenant_id}/",
        }
        if issuer not in valid_issuers:
            raise AuthenticationError("Invalid Entra access token")

    def _principal_from_claims(self, claims: dict[str, Any]) -> Principal:
        subject = claims.get("oid") or claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise AuthenticationError("Invalid Entra access token")

        roles = claims.get("roles", [])
        if not isinstance(roles, list):
            roles = []

        scopes = claims.get("scp", "")
        if not isinstance(scopes, str):
            scopes = ""

        app_id = claims.get("azp") or claims.get("appid")
        name = claims.get("name")

        return Principal(
            subject=subject,
            tenant_id=claims["tid"],
            roles=frozenset(str(role) for role in roles),
            scopes=frozenset(scope for scope in scopes.split() if scope),
            app_id=app_id if isinstance(app_id, str) else None,
            name=name if isinstance(name, str) else None,
            claims=claims,
        )
