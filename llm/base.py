from typing import Any, Protocol


class ToolCaller(Protocol):
    def call_tool(
        self,
        *,
        agent_name: str,
        system: str,
        user_content: str,
        tool_name: str,
        tool_description: str,
        input_schema: dict[str, Any],
    ) -> dict[str, Any]: ...
