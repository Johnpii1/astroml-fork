"""Anthropic Provider implementation."""
from typing import Any, Dict, Iterator, List
from .base import LLMProvider

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        super().__init__(api_key, model)

    def _generate_raw(self, prompt: str, **kwargs: Any) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)
        max_tokens = kwargs.pop("max_tokens", 1024)
        response = client.messages.create(
            model=kwargs.pop("model", self.model),
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        if response.usage is not None:
            self.last_usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            }
        else:
            # Fallback estimation
            p_tokens = self.count_tokens(prompt)
            c_tokens = 100
            self.last_usage = {
                "prompt_tokens": p_tokens,
                "completion_tokens": c_tokens,
                "total_tokens": p_tokens + c_tokens
            }
        return "".join(block.text for block in response.content if hasattr(block, "text"))

    def get_token_usage(self) -> Dict[str, int]:
        return self.last_usage

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)
        max_tokens = kwargs.pop("max_tokens", 1024)
        response = client.messages.create(
            model=kwargs.pop("model", self.model),
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **kwargs,
        )
        for chunk in response:
            if chunk.type == "content_block_delta" and hasattr(chunk.delta, "text"):
                yield chunk.delta.text

    def embed(self, text: str, **kwargs: Any) -> List[float]:
        # Anthropic does not have a native embedding API.
        # Fall back to returning a mock vector of 1536 dimensions.
        return [0.0] * 1536

    def count_tokens(self, text: str) -> int:
        # Approximate (~4 chars/token)
        return max(1, len(text) // 4)
