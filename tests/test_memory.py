from datetime import UTC, datetime

import pytest

from azure_agent_harness.memory.base import Episode
from azure_agent_harness.memory.in_memory import InMemoryEpisodicMemory


@pytest.mark.asyncio
async def test_recent_memory_is_reverse_chronological():
    memory = InMemoryEpisodicMemory()
    for n in range(3):
        await memory.write(
            Episode(
                actor_id="customer-1",
                agent_name="support",
                event=f"event-{n}",
                summary=f"summary-{n}",
                outcome="ok",
                occurred_at=datetime.now(UTC),
            )
        )

    recent = await memory.recent("customer-1", limit=2)
    assert [episode.event for episode in recent] == ["event-2", "event-1"]
