from __future__ import annotations

import hashlib
from typing import Any

import azure.functions as func
from agent_framework_azurefunctions import AgentFunctionApp
from agent_framework_azurefunctions._errors import IncomingRequestError
from agent_framework_durabletask import AgentSessionId

from azure_agent_harness.auth import (
    PRINCIPAL_OPTION_KEY,
    AuthenticationError,
    EntraTokenValidator,
    get_current_principal,
    principal_to_dict,
)
from azure_agent_harness.auth.principal import (
    reset_current_principal,
    set_current_principal,
)
from azure_agent_harness.config import Settings


class HarnessAgentFunctionApp(AgentFunctionApp):
    """AgentFunctionApp with harness Entra principal propagation.

    This class overrides private hooks from the beta Azure Functions integration,
    pinned below 1.1 in pyproject. The repo acceptance tests guard that contract.
    """

    def __init__(
        self,
        *args: Any,
        settings: Settings | None = None,
        validator: EntraTokenValidator | None = None,
        **kwargs: Any,
    ) -> None:
        self.settings = settings or Settings()
        self.settings.validate_auth()
        self._auth_mode = self.settings.auth_mode.strip().lower()

        if self._auth_mode == "entra" and kwargs.get("enable_mcp_tool_trigger") is True:
            raise RuntimeError(
                "Azure Functions MCP tool triggers cannot carry Entra user principals"
            )

        self._validator = (
            validator
            if validator is not None
            else EntraTokenValidator.from_settings(self.settings)
            if self._auth_mode == "entra"
            else None
        )
        super().__init__(*args, **kwargs)

    def _parse_incoming_request(self, req: func.HttpRequest) -> tuple[dict[str, Any], str, str]:
        if self._auth_mode != "entra":
            return super()._parse_incoming_request(req)

        token = self._bearer_token(req)
        if token is None:
            raise IncomingRequestError("Missing bearer token", status_code=401)

        try:
            principal = self._validator.validate(token) if self._validator is not None else None
        except AuthenticationError as exc:
            raise IncomingRequestError("Invalid bearer token", status_code=401) from exc

        context_token = set_current_principal(principal)
        try:
            return super()._parse_incoming_request(req)
        except Exception:
            reset_current_principal(context_token)
            raise

    def _build_request_data(
        self,
        req_body: dict[str, Any],
        message: str,
        correlation_id: str,
        request_response_format: str,
    ) -> dict[str, Any]:
        data = super()._build_request_data(
            req_body,
            message,
            correlation_id,
            request_response_format,
        )
        options = dict(data.get("options") or {})
        options.pop(PRINCIPAL_OPTION_KEY, None)

        if self._auth_mode == "entra":
            principal = get_current_principal()
            if principal is not None:
                options[PRINCIPAL_OPTION_KEY] = principal_to_dict(principal)

        data["options"] = options
        return data

    def _create_session_id(self, agent_name: str, session_key: str | None) -> AgentSessionId:
        if self._auth_mode == "entra" and session_key:
            principal = get_current_principal()
            if principal is not None:
                scope = hashlib.sha256(
                    f"{principal.tenant_id}:{principal.subject}".encode()
                ).hexdigest()[:16]
                return AgentSessionId(name=agent_name, key=f"{scope}-{session_key}")

        return super()._create_session_id(agent_name, session_key)

    @staticmethod
    def _bearer_token(req: func.HttpRequest) -> str | None:
        for key, value in req.headers.items():
            if key.lower() != "authorization":
                continue
            scheme, _, token = value.partition(" ")
            if scheme.lower() == "bearer" and token.strip():
                return token.strip()
            return None
        return None
