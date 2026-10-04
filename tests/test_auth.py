from __future__ import annotations

import asyncio
import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from azure_agent_harness.auth import (
    ROLE_FOR_RISK,
    AuthenticationError,
    EntraAuthMiddleware,
    EntraTokenValidator,
    Principal,
)
from azure_agent_harness.tools.registry import ToolRisk, harness_tool

TENANT = "11111111-1111-1111-1111-111111111111"
OTHER_TENANT = "22222222-2222-2222-2222-222222222222"
AUDIENCE = "api://azure-agent-harness"

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class _SigningKey:
    def __init__(self, key):
        self.key = key


class FakeJwksClient:
    def get_signing_key_from_jwt(self, token):
        return _SigningKey(KEY.public_key())


def make_token(**overrides) -> str:
    now = int(time.time())
    claims = {
        "iss": f"https://login.microsoftonline.com/{TENANT}/v2.0",
        "aud": AUDIENCE,
        "tid": TENANT,
        "oid": "user-object-id",
        "roles": ["Tools.Read"],
        "scp": "Tools.Write",
        "nbf": now,
        "exp": now + 3600,
    }
    claims.update(overrides)
    return jwt.encode(claims, KEY, algorithm="RS256", headers={"kid": "test"})


def make_validator() -> EntraTokenValidator:
    return EntraTokenValidator(
        tenant_id=TENANT,
        audiences=[AUDIENCE],
        jwks_client=FakeJwksClient(),
    )


def test_valid_token_maps_to_principal():
    principal = make_validator().validate(make_token())
    assert principal.subject == "user-object-id"
    assert principal.tenant_id == TENANT
    assert principal.roles == frozenset({"Tools.Read"})
    assert principal.scopes == frozenset({"Tools.Write"})


def test_expired_token_is_rejected():
    with pytest.raises(AuthenticationError):
        make_validator().validate(make_token(exp=int(time.time()) - 3600))


def test_wrong_tenant_is_rejected():
    with pytest.raises(AuthenticationError):
        make_validator().validate(
            make_token(
                tid=OTHER_TENANT,
                iss=f"https://login.microsoftonline.com/{OTHER_TENANT}/v2.0",
            )
        )


def test_role_mapping_is_flat():
    assert ROLE_FOR_RISK == {
        ToolRisk.READ: "Tools.Read",
        ToolRisk.WRITE: "Tools.Write",
        ToolRisk.FINANCIAL: "Tools.Financial",
        ToolRisk.DESTRUCTIVE: "Tools.Destructive",
    }


@harness_tool(name="auth_test_read", description="read", risk=ToolRisk.READ)
def auth_test_read() -> str:
    return "ok"


async def downstream(scope, receive, send):
    principal = scope["state"]["principal"]
    assert isinstance(principal, Principal)
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send(
        {"type": "http.response.body", "body": json.dumps({"sub": principal.subject}).encode()}
    )


def call_app(headers=None):
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    app = EntraAuthMiddleware(downstream, validator=make_validator())
    scope = {
        "type": "http",
        "path": "/responses",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
    }
    asyncio.run(app(scope, receive, send))
    status = next(
        message["status"] for message in messages if message["type"] == "http.response.start"
    )
    body = b"".join(message.get("body", b"") for message in messages)
    return status, body


def test_middleware_rejects_missing_bearer_token():
    status, body = call_app()
    assert status == 401
    assert json.loads(body) == {"error": "unauthorized"}


def test_middleware_accepts_valid_bearer_token():
    status, body = call_app({"Authorization": f"Bearer {make_token()}"})
    assert status == 200
    assert json.loads(body) == {"sub": "user-object-id"}
