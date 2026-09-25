from typing import Annotated

from pydantic import Field

from azure_agent_harness.tools.registry import ToolRisk, harness_tool


@harness_tool(
    name="service_status",
    description="Return the health status for a named demo service.",
    risk=ToolRisk.READ,
)
def get_service_status(
    service: Annotated[str, Field(description="Service name to inspect")],
) -> str:
    """Demo read-only tool. Replace with a real integration in your agent."""
    return f"{service}: healthy (demo response)"


@harness_tool(
    name="create_demo_ticket",
    description="Create a demo support ticket. This illustrates an external write requiring approval.",
    risk=ToolRisk.WRITE,
    approval_mode="always_require",
)
def create_demo_ticket(
    title: Annotated[str, Field(description="Short ticket title")],
) -> str:
    """Demo write tool. A real implementation must also be idempotent and authenticated."""
    return f"DEMO-TICKET created for: {title}"
