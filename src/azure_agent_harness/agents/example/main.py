from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

from azure_agent_harness.llmops.observability import configure_observability
from azure_agent_harness.runtime.factory import build_agent
from azure_agent_harness.tools.example import create_demo_ticket, get_service_status

INSTRUCTIONS = Path(__file__).with_name("instructions.md").read_text()


async def _run(prompt: str) -> None:
    load_dotenv()
    configure_observability()

    agent = build_agent(
        name="example-agent",
        instructions=INSTRUCTIONS,
        tools=[get_service_status, create_demo_ticket],
    )
    response = await agent.run(prompt)
    print(response.text)


def main() -> None:
    prompt = " ".join(sys.argv[1:]).strip() or "What can you do?"
    asyncio.run(_run(prompt))


if __name__ == "__main__":
    main()
