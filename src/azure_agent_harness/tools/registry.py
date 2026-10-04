from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from functools import wraps
from typing import Any

from agent_framework import tool


class ToolRisk(StrEnum):
    READ = "read"
    WRITE = "write"
    FINANCIAL = "financial"
    DESTRUCTIVE = "destructive"


@dataclass(frozen=True)
class ToolMetadata:
    name: str
    risk: ToolRisk
    approval_mode: str
    description: str


_REGISTRY: dict[str, ToolMetadata] = {}


def registered_tools() -> dict[str, ToolMetadata]:
    return dict(_REGISTRY)


def harness_tool(
    *,
    name: str,
    description: str,
    risk: ToolRisk = ToolRisk.READ,
    approval_mode: str | None = None,
) -> Callable[[Callable[..., Any]], Any]:
    """Register risk metadata and create an Agent Framework function tool.

    The approval setting is intentionally explicit. High-risk business rules must
    still be enforced inside deterministic application code at the action boundary.
    """
    if approval_mode is None:
        approval_mode = "never_require" if risk == ToolRisk.READ else "always_require"

    def decorator(fn: Callable[..., Any]) -> Any:
        _REGISTRY[name] = ToolMetadata(
            name=name,
            risk=risk,
            approval_mode=approval_mode,
            description=description,
        )

        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                from azure_agent_harness.auth import authorize_tool_call

                authorize_tool_call(name)
                return await fn(*args, **kwargs)

            wrapped = async_wrapper
        else:

            @wraps(fn)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                from azure_agent_harness.auth import authorize_tool_call

                authorize_tool_call(name)
                return fn(*args, **kwargs)

            wrapped = sync_wrapper

        return tool(
            name=name,
            description=description,
            approval_mode=approval_mode,
        )(wrapped)

    return decorator
