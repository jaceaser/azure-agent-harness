from __future__ import annotations

import time
from typing import Any

import jwt
from agent_framework import Agent
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.ai.agentserver.responses import ResponsesServerOptions
from azure.ai.agentserver.responses.store._memory import InMemoryResponseProvider
from cryptography.hazmat.primitives.asymmetric import rsa
from fakes import ToolCallingChatClient
from starlette.testclient import TestClient

from azure_agent_harness.auth import EntraAuthMiddleware, EntraTokenValidator, get_current_principal
from azure_agent_harness.tools.registry import ToolRisk, harness_tool

TENANT = "11111111-1111-1111-1111-111111111111"
AUDIENCE = "api://azure-agent-harness"
SUBJECT = "foundry-user-object-id"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
TOOL_CALLS: list[dict[str, Any]] = []


class _SigningKey:
    def __init__(self, key: Any) -> None:
        self.key = key


class _FakeJwksClient:
    def get_signing_key_from_jwt(self, token: str) -> _SigningKey:
        return _SigningKey(KEY.public_key())


@harness_tool(name="foundry_auth_probe_read", description="auth probe", risk=ToolRisk.READ)
def foundry_auth_probe_read(item: str) -> str:
    principal = get_current_principal()
    TOOL_CALLS.append(
        {
            "item": item,
            "subject": principal.subject if principal else None,
            "roles": sorted(principal.roles) if principal else [],
        }
    )
    return f"probe:{item}:{principal.subject if principal else 'missing'}"


def _make_token(*, roles: list[str] | None = None, scopes: str = "", subject: str = SUBJECT) -> str:
    now = int(time.time())
    claims = {
        "iss": f"https://login.microsoftonline.com/{TENANT}/v2.0",
        "aud": AUDIENCE,
        "tid": TENANT,
        "oid": subject,
        "roles": roles or [],
        "scp": scopes,
        "nbf": now,
        "exp": now + 3600,
    }
    return jwt.encode(claims, KEY, algorithm="RS256", headers={"kid": "test"})


def _make_validator() -> EntraTokenValidator:
    return EntraTokenValidator(
        tenant_id=TENANT,
        audiences=[AUDIENCE],
        jwks_client=_FakeJwksClient(),
    )


def _make_server() -> ResponsesHostServer:
    agent = Agent(
        client=ToolCallingChatClient("foundry_auth_probe_read", {"item": "case-123"}),
        name="auth-probe",
        instructions="Call the auth probe.",
        tools=[foundry_auth_probe_read],
    )
    server = ResponsesHostServer(
        agent,
        options=ResponsesServerOptions(default_model="offline-test-model"),
        response_store=InMemoryResponseProvider(),
        configure_observability=None,
    )
    server.add_middleware(EntraAuthMiddleware, validator=_make_validator())
    return server


def _post_response(client: TestClient, token: str | None = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.post(
        "/responses",
        json={"input": "please run the probe", "store": False},
        headers=headers,
    )


def test_missing_token_is_rejected_before_tool_runs(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "entra")
    TOOL_CALLS.clear()

    with TestClient(_make_server()) as client:
        response = _post_response(client)

    assert response.status_code == 401
    assert response.json() == {"error": "unauthorized"}
    assert TOOL_CALLS == []


def test_valid_read_role_reaches_tool_with_principal(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "entra")
    TOOL_CALLS.clear()

    with TestClient(_make_server()) as client:
        response = _post_response(client, _make_token(roles=["Tools.Read"]))

    assert response.status_code == 200, response.text
    assert TOOL_CALLS == [
        {"item": "case-123", "subject": SUBJECT, "roles": ["Tools.Read"]},
    ]
    assert f"probe:case-123:{SUBJECT}" in response.text


def test_valid_token_without_read_role_does_not_run_tool_body(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "entra")
    TOOL_CALLS.clear()

    with TestClient(_make_server()) as client:
        response = _post_response(client, _make_token(roles=["Tools.Write"]))

    assert response.status_code == 200, response.text
    assert TOOL_CALLS == []
    assert "Error: Function failed." in response.text


def test_readiness_is_anonymous(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "entra")
    TOOL_CALLS.clear()

    with TestClient(_make_server()) as client:
        response = client.get("/readiness")

    assert response.status_code == 200
    assert TOOL_CALLS == []
