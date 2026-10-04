from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Any

PRINCIPAL_OPTION_KEY = "harness_principal"


@dataclass(frozen=True)
class Principal:
    subject: str
    tenant_id: str
    roles: frozenset[str] = frozenset()
    scopes: frozenset[str] = frozenset()
    app_id: str | None = None
    name: str | None = None
    claims: Mapping[str, Any] = field(default_factory=dict)

    def grants(self, permission: str) -> bool:
        return permission in self.roles or permission in self.scopes


_CURRENT_PRINCIPAL: ContextVar[Principal | None] = ContextVar(
    "azure_agent_harness_current_principal",
    default=None,
)


def get_current_principal() -> Principal | None:
    return _CURRENT_PRINCIPAL.get()


def set_current_principal(principal: Principal | None) -> Token[Principal | None]:
    return _CURRENT_PRINCIPAL.set(principal)


def reset_current_principal(token: Token[Principal | None]) -> None:
    _CURRENT_PRINCIPAL.reset(token)


def principal_to_dict(principal: Principal) -> dict[str, Any]:
    return {
        "subject": principal.subject,
        "tenant_id": principal.tenant_id,
        "roles": sorted(principal.roles),
        "scopes": sorted(principal.scopes),
        "app_id": principal.app_id,
        "name": principal.name,
    }


def _string_set(value: Any) -> frozenset[str]:
    if not isinstance(value, Iterable) or isinstance(value, str | bytes):
        return frozenset()
    return frozenset(str(item) for item in value)


def principal_from_dict(data: Mapping[str, Any]) -> Principal:
    subject = data.get("subject")
    tenant_id = data.get("tenant_id")

    return Principal(
        subject=subject if isinstance(subject, str) else "",
        tenant_id=tenant_id if isinstance(tenant_id, str) else "",
        roles=_string_set(data.get("roles", [])),
        scopes=_string_set(data.get("scopes", [])),
        app_id=data.get("app_id") if isinstance(data.get("app_id"), str) else None,
        name=data.get("name") if isinstance(data.get("name"), str) else None,
        claims={},
    )


@contextmanager
def principal_context(principal: Principal) -> Iterator[None]:
    token = _CURRENT_PRINCIPAL.set(principal)
    try:
        yield
    finally:
        _CURRENT_PRINCIPAL.reset(token)
