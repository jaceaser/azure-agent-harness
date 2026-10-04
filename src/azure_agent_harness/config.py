from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


def _env(name: str, default: str = "", *, normalize: bool = False) -> Any:
    """Read the environment when Settings() is created, not when this module is imported.

    Hosts call load_dotenv() after importing this module, so import-time defaults
    would silently ignore .env values such as AUTH_MODE and APP_ENV.
    """
    def read() -> str:
        value = os.getenv(name, default)
        return value.strip().lower() if normalize else value

    return field(default_factory=read)


def _bool(name: str, default: bool = False) -> Any:
    return field(
        default_factory=lambda: os.getenv(name, str(default)).strip().lower()
        in {"1", "true", "yes", "on"}
    )


@dataclass(frozen=True)
class Settings:
    app_env: str = _env("APP_ENV", "development")
    agent_version: str = _env("AGENT_VERSION", "0.1.0")
    prompt_version: str = _env("PROMPT_VERSION", "example-v1")
    policy_version: str = _env("POLICY_VERSION", "example-v1")

    auth_mode: str = _env("AUTH_MODE", "disabled", normalize=True)
    entra_tenant_id: str = _env("ENTRA_TENANT_ID", "")
    entra_api_audience: str = _env("ENTRA_API_AUDIENCE", "")
    entra_allowed_tenant_ids: str = _env("ENTRA_ALLOWED_TENANT_IDS", "")

    foundry_project_endpoint: str = _env("FOUNDRY_PROJECT_ENDPOINT", "")
    model_deployment: str = _env("AZURE_AI_MODEL_DEPLOYMENT_NAME", "")

    use_managed_identity: bool = _bool("USE_MANAGED_IDENTITY")
    managed_identity_client_id: str = _env("AZURE_CLIENT_ID", "")

    application_insights_connection_string: str = _env("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
    otel_service_name: str = _env("OTEL_SERVICE_NAME", "azure-agent-harness")

    @property
    def entra_audiences(self) -> tuple[str, ...]:
        return tuple(
            audience.strip()
            for audience in self.entra_api_audience.split(",")
            if audience.strip()
        )

    @property
    def entra_allowed_tenants(self) -> tuple[str, ...]:
        allowed = tuple(
            tenant.strip()
            for tenant in self.entra_allowed_tenant_ids.split(",")
            if tenant.strip()
        )
        if allowed:
            return allowed
        return (self.entra_tenant_id,) if self.entra_tenant_id else ()

    def validate_for_cloud_agent(self) -> None:
        missing: list[str] = []
        if not self.foundry_project_endpoint:
            missing.append("FOUNDRY_PROJECT_ENDPOINT")
        if not self.model_deployment:
            missing.append("AZURE_AI_MODEL_DEPLOYMENT_NAME")
        if missing:
            raise RuntimeError(f"Missing required configuration: {', '.join(missing)}")

    def validate_auth(self) -> None:
        auth_mode = self.auth_mode.strip().lower()
        if auth_mode not in {"disabled", "entra"}:
            raise RuntimeError("Invalid AUTH_MODE configuration: expected disabled or entra")
        if self.app_env.strip().lower() == "production" and auth_mode != "entra":
            raise RuntimeError("AUTH_MODE=entra is required when APP_ENV=production")
        if auth_mode == "entra":
            missing: list[str] = []
            if not self.entra_tenant_id:
                missing.append("ENTRA_TENANT_ID")
            if not self.entra_api_audience:
                missing.append("ENTRA_API_AUDIENCE")
            if missing:
                raise RuntimeError(f"Missing required configuration: {', '.join(missing)}")
