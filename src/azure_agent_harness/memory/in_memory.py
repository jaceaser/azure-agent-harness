from __future__ import annotations

from collections import defaultdict

from azure_agent_harness.memory.base import Episode


class InMemoryEpisodicMemory:
    def __init__(self) -> None:
        self._episodes: dict[str, list[Episode]] = defaultdict(list)

    async def write(self, episode: Episode) -> None:
        self._episodes[episode.actor_id].append(episode)

    async def recent(self, actor_id: str, limit: int = 20) -> list[Episode]:
        return list(reversed(self._episodes.get(actor_id, [])))[:limit]
