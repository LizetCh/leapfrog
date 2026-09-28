import json
import logging
import os
import time
from typing import Any

from google import genai
from google.genai import errors, types

from .pricing import cost_usd

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
MAX_OUTPUT_TOKENS = 2048
MAX_RETRIES = 4
BASE_DELAY_SECONDS = 1.0

logger = logging.getLogger("leapfrog")


class GeminiToolCaller:
    def __init__(self) -> None:
        self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

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
        function = types.FunctionDeclaration(
            name=tool_name,
            description=tool_description,
            parameters_json_schema=input_schema,
        )
        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            tools=[types.Tool(function_declarations=[function])],
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="ANY",
                    allowed_function_names=[tool_name],
                )
            ),
        )

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            start = time.monotonic()
            try:
                response = self._client.models.generate_content(
                    model=MODEL,
                    contents=user_content,
                    config=config,
                )
            except errors.APIError as exc:
                last_error = exc
                if attempt == MAX_RETRIES - 1:
                    break
                time.sleep(BASE_DELAY_SECONDS * (2**attempt))
                continue

            latency_ms = int((time.monotonic() - start) * 1000)
            usage = response.usage_metadata
            logger.info(json.dumps({
                "agent": agent_name,
                "provider": "gemini",
                "latency_ms": latency_ms,
                "input_tokens": usage.prompt_token_count,
                "output_tokens": usage.candidates_token_count,
                "estimated_cost_usd": round(
                    cost_usd(MODEL, usage.prompt_token_count, usage.candidates_token_count), 6
                ),
            }))

            for part in response.candidates[0].content.parts:
                if part.function_call is not None and part.function_call.name == tool_name:
                    return dict(part.function_call.args)
            raise RuntimeError(f"{agent_name}: model response did not call tool '{tool_name}'")

        raise RuntimeError(f"{agent_name}: Gemini API failed after {MAX_RETRIES} attempts") from last_error
