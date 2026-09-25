from __future__ import annotations

from dataclasses import asdict, dataclass

from azure_agent_harness.config import Settings


@dataclass(frozen=True)
class RunVersionMetadata:
    agent_version: str
    prompt_version: str
    policy_version: str
    model_deployment: str


def current_version_metadata(settings: Settings | None = None) -> dict[str, str]:
    settings = settings or Settings()
    return asdict(
        RunVersionMetadata(
            agent_version=settings.agent_version,
            prompt_version=settings.prompt_version,
            policy_version=settings.policy_version,
            model_deployment=settings.model_deployment,
        )
    )
