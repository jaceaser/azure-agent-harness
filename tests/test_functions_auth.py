from __future__ import annotations

import asyncio
import contextvars
import json
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import azure.functions as func
import jwt
import pytest
from agent_framework import Agent, AgentContext
from agent_framework_azurefunctions._errors import IncomingRequestError
from cryptography.hazmat.primitives.asymmetric import rsa

sys.path.insert(0, str(Path(__file__).parent))
from fakes import ToolCallingChatClient  # noqa: E402

from azure_agent_harness.auth import (  # noqa: E402
    PRINCIPAL_OPTION_KEY,
    EntraTokenValidator,
    Principal,
    PrincipalOptionsMiddleware,
    get_current_principal,
    principal_context,
    principal_from_dict,
    principal_to_dict,
)
from azure_agent_harness.config import Settings  # noqa: E402
from azure_agent_harness.hosting.functions import HarnessAgentFunctionApp  # noqa: E402
from azure_agent_harness.tools.registry import ToolRisk, harness_tool  # noqa: E402

TENANT = "11111111-1111-1111-1111-111111111111"
AUDIENCE = "api://azure-agent-harness"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
CALLS: list[tuple[str, str | None]] = []


class _SigningKey:
    key = KEY.public_key()


class _Jwks:
    def get_signing_key_from_jwt(self, token: str) -> _SigningKey:
        return _SigningKey()


@harness_tool(name="functions_auth_probe_read", description="probe", risk=ToolRisk.READ)
def functions_auth_probe_read(item: str) -> str:
    principal = get_current_principal()
    CALLS.append((item, principal.subject if principal else None))
    return f"probe:{item}"


def _token(*, subject: str = "alice-oid", roles: tuple[str, ...] = ("Tools.Read",)) -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "iss": f"https://login.microsoftonline.com/{TENANT}/v2.0",
            "aud": AUDIENCE,
            "tid": TENANT,
            "oid": subject,
            "roles": list(roles),
            "iat": now,
            "nbf": now,
            "exp": now + 600,
        },
        KEY,
        algorithm="RS256",
        headers={"kid": "test"},
    )


def _settings(auth_mode: str = "entra") -> Settings:
    return replace(
        Settings(),
        auth_mode=auth_mode,
        app_env="development",
        entra_tenant_id=TENANT,
        entra_api_audience=AUDIENCE,
    )


def _validator() -> EntraTokenValidator:
    return EntraTokenValidator(tenant_id=TENANT, audiences=[AUDIENCE], jwks_client=_Jwks())


def _agent(**kwargs: Any) -> Agent:
    return Agent(
        client=ToolCallingChatClient("functions_auth_probe_read", {"item": "case-1"}),
        name="probe",
        instructions="Call the probe.",
        tools=[functions_auth_probe_read],
        **kwargs,
    )


def _app(settings: Settings | None = None, **kwargs: Any) -> HarnessAgentFunctionApp:
    return HarnessAgentFunctionApp(
        agents=[_agent(middleware=[PrincipalOptionsMiddleware()])],
        settings=settings or _settings(),
        validator=_validator(),
        **kwargs,
    )


def _req(
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
) -> func.HttpRequest:
    return func.HttpRequest(
        "POST",
        "http://localhost/api/agents/probe/run",
        headers={"Content-Type": "application/json", **(headers or {})},
        body=json.dumps(body or {"message": "hi"}).encode(),
    )


def _fresh(fn):
    return contextvars.copy_context().run(fn)


def _run(agent: Agent, **kwargs: Any) -> None:
    asyncio.run(agent.run("hi", **kwargs))


def test_principal_serializes_without_raw_claims() -> None:
    principal = Principal(
        subject="subject",
        tenant_id="tenant",
        roles=frozenset({"Tools.Read"}),
        scopes=frozenset({"Tools.Write"}),
        app_id="app",
        name="name",
        claims={"secret": "never persist this"},
    )

    payload = principal_to_dict(principal)
    assert PRINCIPAL_OPTION_KEY == "harness_principal"
    assert "claims" not in payload
    assert "secret" not in json.dumps(payload)

    restored = principal_from_dict(payload)
    assert restored == Principal(
        subject="subject",
        tenant_id="tenant",
        roles=frozenset({"Tools.Read"}),
        scopes=frozenset({"Tools.Write"}),
        app_id="app",
        name="name",
        claims={},
    )


def test_options_principal_reaches_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_MODE", "entra")
    CALLS.clear()
    payload = principal_to_dict(
        Principal(subject="bob", tenant_id=TENANT, roles=frozenset({"Tools.Read"}))
    )

    _fresh(
        lambda: _run(
            _agent(middleware=[PrincipalOptionsMiddleware()]),
            options={PRINCIPAL_OPTION_KEY: payload},
        )
    )

    assert CALLS == [("case-1", "bob")]


def test_context_principal_wins_and_option_is_stripped() -> None:
    seen: dict[str, Any] = {}
    real = Principal(subject="carol", tenant_id=TENANT, roles=frozenset({"Tools.Read"}))
    forged = principal_to_dict(
        Principal(subject="mallory", tenant_id=TENANT, roles=frozenset({"Tools.Read"}))
    )

    async def run_middleware() -> None:
        ctx = AgentContext(
            agent=_agent(),
            messages=[],
            options={PRINCIPAL_OPTION_KEY: forged, "temperature": 0},
        )

        async def call_next() -> None:
            seen["options"] = dict(ctx.options or {})
            seen["principal"] = get_current_principal()

        with principal_context(real):
            await PrincipalOptionsMiddleware().process(ctx, call_next)

    _fresh(lambda: asyncio.run(run_middleware()))

    assert seen["principal"].subject == "carol"
    assert PRINCIPAL_OPTION_KEY not in seen["options"]
    assert seen["options"] == {"temperature": 0}


def test_missing_token_is_401() -> None:
    app = _app()

    def go() -> None:
        with pytest.raises(IncomingRequestError) as exc:
            app._parse_incoming_request(_req())
        assert exc.value.status_code == 401

    _fresh(go)


def test_valid_token_becomes_run_request_option() -> None:
    app = _app()

    def go() -> None:
        body, message, fmt = app._parse_incoming_request(
            _req({"authorization": f"Bearer {_token()}"})
        )
        data = app._build_request_data(body, message, "corr-1", fmt)
        payload = data["options"][PRINCIPAL_OPTION_KEY]
        assert payload["subject"] == "alice-oid"
        assert payload["roles"] == ["Tools.Read"]
        json.dumps(data)

    _fresh(go)


def test_body_cannot_forge_principal_option() -> None:
    app = _app()
    forged = {
        "message": "hi",
        "options": {
            PRINCIPAL_OPTION_KEY: {
                "subject": "mallory",
                "tenant_id": TENANT,
                "roles": ["Tools.Destructive"],
            }
        },
    }

    def go() -> None:
        body, message, fmt = app._parse_incoming_request(
            _req({"Authorization": f"Bearer {_token()}"}, forged)
        )
        data = app._build_request_data(body, message, "corr-1", fmt)
        assert data["options"][PRINCIPAL_OPTION_KEY]["subject"] == "alice-oid"

    _fresh(go)


def test_sessions_are_scoped_per_principal() -> None:
    app = _app()

    def key_for(subject: str) -> str:
        def go() -> str:
            app._parse_incoming_request(
                _req({"Authorization": f"Bearer {_token(subject=subject)}"})
            )
            return app._create_session_id("probe", "shared").key

        return _fresh(go)

    assert key_for("alice-oid") == key_for("alice-oid")
    assert key_for("alice-oid") != key_for("bob-oid")


def test_disabled_mode_passthrough() -> None:
    app = _app(settings=_settings("disabled"))

    def go() -> None:
        body, message, fmt = app._parse_incoming_request(_req())
        data = app._build_request_data(body, message, "corr-1", fmt)
        assert PRINCIPAL_OPTION_KEY not in (data.get("options") or {})
        assert app._create_session_id("probe", "shared").key == "shared"

    _fresh(go)


def test_mcp_trigger_is_refused_in_entra_mode() -> None:
    with pytest.raises(RuntimeError):
        _app(enable_mcp_tool_trigger=True)
