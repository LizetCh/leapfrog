import json
import logging
import os
import time
from typing import Any

import anthropic
from anthropic import APIConnectionError, APIStatusError

from .pricing import cost_usd

MODEL = "claude-sonnet-5"
MAX_RETRIES = 4
BASE_DELAY_SECONDS = 1.0

logger = logging.getLogger("leapfrog")


class AnthropicToolCaller:
    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def call_tool(
        self,
        *,
        agent_name: str,
        system: str,
        user_content: str,
        tool_name: str,
        tool_description: str,
        input_schema: dict[str, Any],
    ) -> dict[str, Any]:
        tool = {"name": tool_name, "description": tool_description, "input_schema": input_schema}

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            start = time.monotonic()
            try:
                response = self._client.messages.create(
                    model=MODEL,
                    max_tokens=2048,
                    system=system,
                    messages=[{"role": "user", "content": user_content}],
                    tools=[tool],
                    tool_choice={"type": "tool", "name": tool_name},
                )
            except (APIStatusError, APIConnectionError) as exc:
                last_error = exc
                if attempt == MAX_RETRIES - 1:
                    break
                time.sleep(BASE_DELAY_SECONDS * (2**attempt))
                continue

            latency_ms = int((time.monotonic() - start) * 1000)
            usage = response.usage
            logger.info(json.dumps({
                "agent": agent_name,
                "provider": "anthropic",
                "latency_ms": latency_ms,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "estimated_cost_usd": round(cost_usd(MODEL, usage.input_tokens, usage.output_tokens), 6),
            }))

            for block in response.content:
                if block.type == "tool_use" and block.name == tool_name:
                    return block.input
            raise RuntimeError(f"{agent_name}: model response did not call tool '{tool_name}'")

        raise RuntimeError(f"{agent_name}: Claude API failed after {MAX_RETRIES} attempts") from last_error
