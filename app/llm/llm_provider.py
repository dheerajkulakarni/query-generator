"""
OpenAI-compatible LLM provider implementation.

Uses the OpenAI Python SDK, which works with any OpenAI-compatible API:
- OpenAI (GPT-4, GPT-3.5, etc.)
- Google Gemini (via OpenAI-compatible endpoint)
- Ollama (local models)
- Azure OpenAI
- Any other provider following the OpenAI API standard
"""

import logging

from openai import OpenAI

from app.config.settings import LLMConfig
from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)

# Default base URLs for known providers
PROVIDER_BASE_URLS = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "openai": "https://api.openai.com/v1",
    "ollama": "http://localhost:11434/v1",
}


class OpenAICompatibleProvider(LLMProvider):
    """
    LLM provider using the OpenAI SDK.

    Works with any API that follows the OpenAI chat completions standard.
    Configure the provider via `base_url` in config or use a known
    provider name (gemini, openai, ollama) for automatic URL resolution.
    """

    def __init__(self, config: LLMConfig) -> None:
        """
        Initialize the OpenAI-compatible client.

        Args:
            config: LLM configuration containing API key, model, base_url, etc.

        Raises:
            ValueError: If no API key is provided (unless using a local provider).
        """
        # Resolve base URL from provider name or explicit config
        base_url = config.base_url or PROVIDER_BASE_URLS.get(
            config.provider, PROVIDER_BASE_URLS["openai"]
        )

        # Local providers (e.g., Ollama) don't need an API key
        api_key = config.api_key or "not-needed"
        if not config.api_key and config.provider not in ("ollama",):
            raise ValueError(
                "LLM API key is required. "
                "Set the LLM_API_KEY environment variable or configure it in config.yaml."
            )

        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = config.model
        self._temperature = config.temperature

        logger.info(
            "OpenAI-compatible provider initialized — model='%s', base_url='%s'",
            self._model,
            base_url,
        )

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Generate a response using the OpenAI chat completions API.

        Args:
            prompt: The user prompt.
            system_prompt: Optional system instruction.

        Returns:
            The generated text response.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=self._temperature,
        )

        return response.choices[0].message.content or ""
