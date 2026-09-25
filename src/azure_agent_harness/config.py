from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    agent_version: str = os.getenv("AGENT_VERSION", "0.1.0")
    prompt_version: str = os.getenv("PROMPT_VERSION", "example-v1")
    policy_version: str = os.getenv("POLICY_VERSION", "example-v1")

    foundry_project_endpoint: str = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "")
    model_deployment: str = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "")

    use_managed_identity: bool = _bool("USE_MANAGED_IDENTITY")
    managed_identity_client_id: str = os.getenv("AZURE_CLIENT_ID", "")

    application_insights_connection_string: str = os.getenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING", ""
    )
    otel_service_name: str = os.getenv("OTEL_SERVICE_NAME", "azure-agent-harness")

    def validate_for_cloud_agent(self) -> None:
        missing: list[str] = []
        if not self.foundry_project_endpoint:
            missing.append("FOUNDRY_PROJECT_ENDPOINT")
        if not self.model_deployment:
            missing.append("AZURE_AI_MODEL_DEPLOYMENT_NAME")
        if missing:
            raise RuntimeError(f"Missing required configuration: {', '.join(missing)}")
