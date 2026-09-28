import json
from pathlib import Path

_PRICING = json.loads((Path(__file__).parent / "pricing.json").read_text())["prices_usd_per_1k_tokens"]


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    prices = _PRICING.get(model, {"input": 0.0, "output": 0.0})
    return (input_tokens / 1000) * prices["input"] + (output_tokens / 1000) * prices["output"]
