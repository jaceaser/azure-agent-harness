from __future__ import annotations

from agent_framework_foundry_hosting import ResponsesHostServer
from dotenv import load_dotenv

from azure_agent_harness.agents.example.main import INSTRUCTIONS
from azure_agent_harness.auth import EntraAuthMiddleware, EntraTokenValidator
from azure_agent_harness.config import Settings
from azure_agent_harness.llmops.observability import configure_observability
from azure_agent_harness.runtime.factory import build_agent
from azure_agent_harness.tools.example import create_demo_ticket, get_service_status


def main() -> None:
    load_dotenv()
    settings = Settings()
    settings.validate_auth()
    configure_observability()

    agent = build_agent(
        name="example-agent",
        instructions=INSTRUCTIONS,
        tools=[get_service_status, create_demo_ticket],
    )
    server = ResponsesHostServer(agent)
    if settings.auth_mode == "entra":
        server.add_middleware(
            EntraAuthMiddleware,
            validator=EntraTokenValidator.from_settings(settings),
        )
    server.run()


if __name__ == "__main__":
    main()
