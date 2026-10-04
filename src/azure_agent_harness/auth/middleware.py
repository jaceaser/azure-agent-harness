from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable, Iterable
from typing import Any

from azure_agent_harness.auth.principal import principal_context
from azure_agent_harness.auth.validator import AuthenticationError, EntraTokenValidator

AsgiMessage = dict[str, Any]
AsgiReceive = Callable[[], Awaitable[AsgiMessage]]
AsgiSend = Callable[[AsgiMessage], Awaitable[None]]
AsgiApp = Callable[[dict[str, Any], AsgiReceive, AsgiSend], Awaitable[None]]


class EntraAuthMiddleware:
    def __init__(
        self,
        app: AsgiApp,
        *,
        validator: EntraTokenValidator,
        exempt_paths: Iterable[str] = ("/readiness",),
    ) -> None:
        self.app = app
        self.validator = validator
        self.exempt_paths = frozenset(exempt_paths)

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: AsgiReceive,
        send: AsgiSend,
    ) -> None:
        scope_type = scope.get("type")
        if scope_type not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return

        if scope_type == "http" and scope.get("path") in self.exempt_paths:
            await self.app(scope, receive, send)
            return

        token = self._bearer_token(scope)
        if token is None:
            await self._reject(scope_type, send, invalid_token=False)
            return

        try:
            principal = await asyncio.to_thread(self.validator.validate, token)
        except AuthenticationError:
            await self._reject(scope_type, send, invalid_token=True)
            return

        scope.setdefault("state", {})["principal"] = principal
        with principal_context(principal):
            await self.app(scope, receive, send)

    def _bearer_token(self, scope: dict[str, Any]) -> str | None:
        for name, value in scope.get("headers", []):
            if name.lower() != b"authorization":
                continue
            scheme, _, token = value.decode("latin1").partition(" ")
            if scheme.lower() == "bearer" and token:
                return token.strip()
            return None
        return None

    async def _reject(self, scope_type: str, send: AsgiSend, *, invalid_token: bool) -> None:
        if scope_type == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return

        challenge = 'Bearer error="invalid_token"' if invalid_token else "Bearer"
        body = json.dumps({"error": "unauthorized"}).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"www-authenticate", challenge.encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
