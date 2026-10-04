from __future__ import annotations

import asyncio
import json
from pathlib import Path

from agent_framework import evaluate_agent
from agent_framework.foundry import FoundryEvals
from dotenv import load_dotenv

from azure_agent_harness.agents.example.main import INSTRUCTIONS
from azure_agent_harness.runtime.factory import build_agent
from azure_agent_harness.tools.example import get_service_status

DATASET = Path(__file__).resolve().parents[3] / "llmops" / "datasets" / "cloud_smoke.jsonl"


async def main() -> None:
    """Run a small Microsoft Foundry quality gate.

    Keep this dataset intentionally small for pull requests. Larger regression and
    production-trace evaluation suites should run on a schedule or release gate.
    """
    load_dotenv()
    cases = [json.loads(line) for line in DATASET.read_text().splitlines() if line.strip()]

    agent = build_agent(
        name="example-agent-eval",
        instructions=INSTRUCTIONS,
        tools=[get_service_status],
    )

    # Microsoft Agent Framework's current Foundry integration can use the same
    # Foundry chat client backing the agent for managed evaluator calls.
    chat_client = agent.client
    evaluators = FoundryEvals(
        client=chat_client,
        evaluators=[FoundryEvals.RELEVANCE, FoundryEvals.TOOL_CALL_ACCURACY],
    )

    results = await evaluate_agent(
        agent=agent,
        queries=[case["query"] for case in cases],
        evaluators=evaluators,
    )

    for result in results:
        print(f"{result.provider}: {result.passed}/{result.total} passed")
        if getattr(result, "report_url", None):
            print(f"Foundry report: {result.report_url}")
        result.raise_for_status()


if __name__ == "__main__":
    asyncio.run(main())
