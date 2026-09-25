from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

from azure_agent_harness.config import Settings


def _credential(settings: Settings):
    """Choose an Azure credential path.

    Managed Identity can be forced for hardened production deployments. The
    default path matches Microsoft's Hosted Agent samples and supports local CLI,
    workload identity, and managed identity environments through Azure Identity.
    """
    if settings.use_managed_identity:
        if settings.managed_identity_client_id:
            return ManagedIdentityCredential(client_id=settings.managed_identity_client_id)
        return ManagedIdentityCredential()
    return DefaultAzureCredential()


def build_agent(
    *,
    name: str,
    instructions: str,
    tools: Sequence[Any] | None = None,
    settings: Settings | None = None,
) -> Agent:
    """Build a Microsoft Agent Framework agent backed by a Foundry project model."""
    settings = settings or Settings()
    settings.validate_for_cloud_agent()

    client = FoundryChatClient(
        project_endpoint=settings.foundry_project_endpoint,
        model=settings.model_deployment,
        credential=_credential(settings),
    )

    return Agent(
        client=client,
        name=name,
        instructions=instructions,
        tools=list(tools or []),
        # Let the selected host/session strategy own conversation persistence.
        default_options={"store": False},
    )
