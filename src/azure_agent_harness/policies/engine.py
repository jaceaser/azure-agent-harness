from __future__ import annotations

from dataclasses import dataclass, field


class PolicyViolation(RuntimeError):
    pass


@dataclass(frozen=True)
class ToolPolicy:
    prohibited: frozenset[str] = field(default_factory=frozenset)
    approval_required: frozenset[str] = field(default_factory=frozenset)

    def assert_allowed(self, tool_name: str) -> None:
        if tool_name in self.prohibited:
            raise PolicyViolation(f"Tool is prohibited by deterministic policy: {tool_name}")

    def requires_approval(self, tool_name: str) -> bool:
        self.assert_allowed(tool_name)
        return tool_name in self.approval_required
