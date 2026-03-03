"""
Provider factory — selects the correct LLM implementation based on the
LLM_PROVIDER environment variable.
"""
from django.conf import settings

from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .ollama_provider import OllamaProvider


_PROVIDERS = {
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}


def get_llm_provider() -> BaseLLMProvider:
    """
    Return the appropriate LLM provider instance.
    Raises ValueError for unknown provider names.
    """
    provider_name = settings.LLM_PROVIDER.lower()
    cls = _PROVIDERS.get(provider_name)
    if cls is None:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider_name}'. "
            f"Valid options: {list(_PROVIDERS)}"
        )
    return cls()
