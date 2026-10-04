from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class PolicyViolation(RuntimeError):
    pass


@dataclass(frozen=True)
class ToolPolicy:
    prohibited: frozenset[str] = field(default_factory=frozenset)
    approval_required: frozenset[str] = field(default_factory=frozenset)

    def assert_allowed(self, tool_name: str, principal: Any | None = None) -> None:
        if tool_name in self.prohibited:
            raise PolicyViolation(f"Tool is prohibited by deterministic policy: {tool_name}")
        if principal is not None:
            from azure_agent_harness.auth import authorize_tool_call

            authorize_tool_call(tool_name, principal=principal)

    def requires_approval(self, tool_name: str) -> bool:
        self.assert_allowed(tool_name)
        return tool_name in self.approval_required
