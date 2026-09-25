from __future__ import annotations

import os

from azure_agent_harness.config import Settings


def configure_observability(settings: Settings | None = None) -> None:
    """Configure Azure Monitor/OpenTelemetry when a connection string is available.

    Microsoft Foundry-hosted Agent Framework applications can emit native agent
    traces. This bootstrap is useful for custom application spans and self-hosted
    execution paths.
    """
    settings = settings or Settings()
    if not settings.application_insights_connection_string:
        return

    os.environ.setdefault("OTEL_SERVICE_NAME", settings.otel_service_name)

    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "Install the 'foundry' extra to enable Azure Monitor telemetry."
        ) from exc

    configure_azure_monitor(
        connection_string=settings.application_insights_connection_string,
    )
