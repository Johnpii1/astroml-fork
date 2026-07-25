"""OpenAI Provider implementation."""
from typing import Any, Dict, Iterator, List
from .base import LLMProvider

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        super().__init__(api_key, model)

    def _generate_raw(self, prompt: str, **kwargs: Any) -> str:
        import openai
        client = openai.OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=kwargs.pop("model", self.model),
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        if response.usage is not None:
            self.last_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        else:
            # Fallback estimation if usage is not returned
            p_tokens = self.count_tokens(prompt)
            c_tokens = 100 # Default/mock completion length
            self.last_usage = {
                "prompt_tokens": p_tokens,
                "completion_tokens": c_tokens,
                "total_tokens": p_tokens + c_tokens
            }
        return response.choices[0].message.content

    def get_token_usage(self) -> Dict[str, int]:
        return self.last_usage

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        import openai
        client = openai.OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=kwargs.pop("model", self.model),
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **kwargs,
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def embed(self, text: str, **kwargs: Any) -> List[float]:
        import openai
        client = openai.OpenAI(api_key=self.api_key)
        response = client.embeddings.create(
            input=[text],
            model=kwargs.pop("model", "text-embedding-3-small"),
            **kwargs
        )
        return response.data[0].embedding

    def count_tokens(self, text: str) -> int:
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except Exception:
            # Approximate (~4 chars/token)
            return max(1, len(text) // 4)
