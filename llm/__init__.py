import os

from .base import ToolCaller


def get_default_caller() -> ToolCaller:
    provider = os.environ.get("LLM_PROVIDER", "gemini")
    if provider == "gemini":
        from .gemini_client import GeminiToolCaller
        return GeminiToolCaller()
    if provider == "anthropic":
        from .anthropic_client import AnthropicToolCaller
        return AnthropicToolCaller()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
