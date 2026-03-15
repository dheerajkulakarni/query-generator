"""
Abstract base class for LLM provider implementations.

To add a new LLM provider:
1. Create a new file in this package (e.g., `openai_provider.py`).
2. Implement the `LLMProvider` interface.
3. Wire it up via configuration in `main.py`.
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Abstract interface for Large Language Model providers.

    All LLM implementations must inherit from this class
    and implement the `generate` method.
    """

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Generate a text completion from the LLM.

        Args:
            prompt: The user prompt / main instruction.
            system_prompt: Optional system-level instruction for the model.

        Returns:
            The generated text response.
        """
        ...
