from __future__ import annotations

from azure_agent_harness.auth.principal import Principal, get_current_principal
from azure_agent_harness.config import Settings
from azure_agent_harness.policies.engine import PolicyViolation
from azure_agent_harness.tools.registry import ToolRisk, registered_tools


class AuthorizationError(PolicyViolation):
    pass


ROLE_FOR_RISK: dict[ToolRisk, str] = {
    ToolRisk.READ: "Tools.Read",
    ToolRisk.WRITE: "Tools.Write",
    ToolRisk.FINANCIAL: "Tools.Financial",
    ToolRisk.DESTRUCTIVE: "Tools.Destructive",
}


def authorize_tool_call(
    tool_name: str,
    *,
    principal: Principal | None = None,
    settings: Settings | None = None,
) -> None:
    settings = settings or Settings()
    auth_mode = settings.auth_mode.strip().lower()
    principal = principal if principal is not None else get_current_principal()

    if principal is None:
        if auth_mode == "entra":
            raise AuthorizationError("Authentication is required to call tools")
        return

    tools = registered_tools()
    metadata = tools.get(tool_name)
    if metadata is None:
        raise AuthorizationError(f"Tool is not registered: {tool_name}")

    required_role = ROLE_FOR_RISK[metadata.risk]
    if not principal.grants(required_role):
        raise AuthorizationError(f"Tool {tool_name} requires role {required_role}")
