from __future__ import annotations

from collections.abc import AsyncIterator, Mapping, Sequence
from typing import Any

from agent_framework import (
    BaseChatClient,
    ChatResponse,
    ChatResponseUpdate,
    Content,
    FunctionInvocationLayer,
    Message,
    ResponseStream,
)


class ToolCallingChatClient(FunctionInvocationLayer, BaseChatClient):
    """Offline chat client that drives Agent Framework's real tool loop."""

    def __init__(self, tool_name: str, arguments: dict[str, Any]) -> None:
        self.tool_name = tool_name
        self.arguments = dict(arguments)
        self._next_call_index = 0
        super().__init__()

    def _inner_get_response(
        self,
        *,
        messages: Sequence[Message],
        stream: bool,
        options: Mapping[str, Any],
        **kwargs: Any,
    ) -> Any:
        del options, kwargs
        response = self._response_for(messages)
        if not stream:

            async def _response() -> ChatResponse[Any]:
                return response

            return _response()

        async def _updates() -> AsyncIterator[ChatResponseUpdate]:
            for message in response.messages:
                yield ChatResponseUpdate(
                    role=message.role,
                    contents=message.contents,
                    finish_reason=response.finish_reason,
                )

        return ResponseStream(_updates(), finalizer=ChatResponse.from_updates)

    def _response_for(self, messages: Sequence[Message]) -> ChatResponse[Any]:
        if tool_result := self._latest_function_result_text(messages):
            return ChatResponse(
                messages=[Message("assistant", [f"Tool result: {tool_result}"])],
                finish_reason="stop",
            )

        self._next_call_index += 1
        function_call = Content.from_function_call(
            call_id=f"offline-call-{self._next_call_index}",
            name=self.tool_name,
            arguments=self.arguments,
        )
        return ChatResponse(
            messages=[Message("assistant", [function_call])],
            finish_reason="tool_calls",
        )

    @staticmethod
    def _latest_function_result_text(messages: Sequence[Message]) -> str | None:
        for message in reversed(messages):
            for content in reversed(message.contents):
                if content.type == "function_result":
                    result = getattr(content, "result", None)
                    return str(result) if result is not None else ""
        return None
