from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, MutableMapping

from agent_framework import AgentContext, AgentMiddleware

from azure_agent_harness.auth.principal import (
    PRINCIPAL_OPTION_KEY,
    get_current_principal,
    principal_context,
    principal_from_dict,
)


class PrincipalOptionsMiddleware(AgentMiddleware):
    async def process(
        self,
        context: AgentContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        options = context.options
        payload = None

        if isinstance(options, MutableMapping):
            payload = options.pop(PRINCIPAL_OPTION_KEY, None)
        elif options is not None:
            copied = dict(options)
            payload = copied.pop(PRINCIPAL_OPTION_KEY, None)
            context.options = copied

        if get_current_principal() is not None:
            await call_next()
            return

        if not isinstance(payload, Mapping):
            await call_next()
            return

        with principal_context(principal_from_dict(payload)):
            await call_next()
