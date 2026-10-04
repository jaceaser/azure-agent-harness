from __future__ import annotations

from azure_agent_harness.auth.agent_middleware import PrincipalOptionsMiddleware
from azure_agent_harness.auth.authorization import (
    ROLE_FOR_RISK,
    AuthorizationError,
    authorize_tool_call,
)
from azure_agent_harness.auth.middleware import EntraAuthMiddleware
from azure_agent_harness.auth.principal import (
    PRINCIPAL_OPTION_KEY,
    Principal,
    get_current_principal,
    principal_context,
    principal_from_dict,
    principal_to_dict,
)
from azure_agent_harness.auth.validator import AuthenticationError, EntraTokenValidator

__all__ = [
    "ROLE_FOR_RISK",
    "AuthenticationError",
    "AuthorizationError",
    "EntraAuthMiddleware",
    "EntraTokenValidator",
    "PRINCIPAL_OPTION_KEY",
    "Principal",
    "PrincipalOptionsMiddleware",
    "authorize_tool_call",
    "get_current_principal",
    "principal_from_dict",
    "principal_to_dict",
    "principal_context",
]
