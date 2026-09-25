from __future__ import annotations

from dotenv import load_dotenv
from agent_framework_foundry_hosting import ResponsesHostServer

from azure_agent_harness.agents.example.main import INSTRUCTIONS
from azure_agent_harness.llmops.observability import configure_observability
from azure_agent_harness.runtime.factory import build_agent
from azure_agent_harness.tools.example import create_demo_ticket, get_service_status


def main() -> None:
    load_dotenv()
    configure_observability()

    agent = build_agent(
        name="example-agent",
        instructions=INSTRUCTIONS,
        tools=[get_service_status, create_demo_ticket],
    )
    ResponsesHostServer(agent).run()


if __name__ == "__main__":
    main()
