"""Azure Functions / Durable Extension hosting example with harness auth propagation.

Install the `functions` extra and verify the current Agent Framework prerelease/GA
package contract before deploying. This path is intended for workloads that need
Functions triggers or durable orchestration.
"""

from __future__ import annotations

from azure_agent_harness.agents.example.main import INSTRUCTIONS
from azure_agent_harness.auth import PrincipalOptionsMiddleware
from azure_agent_harness.hosting.functions import HarnessAgentFunctionApp
from azure_agent_harness.runtime.factory import build_agent
from azure_agent_harness.tools.example import create_demo_ticket, get_service_status


def create_agent():
    return build_agent(
        name="example-agent",
        instructions=INSTRUCTIONS,
        tools=[get_service_status, create_demo_ticket],
        middleware=[PrincipalOptionsMiddleware()],
    )


app = HarnessAgentFunctionApp(
    agents=[create_agent()],
    enable_health_check=True,
)
