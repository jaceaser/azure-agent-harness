from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class Episode:
    actor_id: str
    agent_name: str
    event: str
    summary: str
    outcome: str
    occurred_at: datetime


class EpisodicMemory(Protocol):
    async def write(self, episode: Episode) -> None: ...

    async def recent(self, actor_id: str, limit: int = 20) -> list[Episode]: ...
