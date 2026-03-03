"""
Ollama local LLM provider.
Sends requests to a locally running Ollama instance via its HTTP API.
"""
import json
import requests
from django.conf import settings

from .base import BaseLLMProvider, ClassificationResult, LLMProviderError
from .prompts import SYSTEM_PROMPT, build_user_message


class OllamaProvider(BaseLLMProvider):
    """Calls a locally running Ollama model for classification and extraction."""

    def __init__(self):
        self._base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self._model = settings.OLLAMA_MODEL
        self._timeout = settings.LLM_TIMEOUT_SECONDS

    @property
    def model_name(self) -> str:
        return f"ollama/{self._model}"

    def classify_and_extract(self, text: str, filename: str) -> ClassificationResult:
        user_message = build_user_message(text, filename)
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "format": "json",
        }
        try:
            resp = requests.post(
                f"{self._base_url}/api/chat",
                json=payload,
                timeout=self._timeout,
            )
            resp.raise_for_status()
        except requests.ConnectionError as exc:
            raise LLMProviderError(
                f"Cannot reach Ollama at {self._base_url}. "
                "Is Ollama running? (`ollama serve`)"
            ) from exc
        except requests.Timeout as exc:
            raise LLMProviderError(
                f"Ollama request timed out after {self._timeout}s."
            ) from exc
        except requests.HTTPError as exc:
            raise LLMProviderError(f"Ollama HTTP error: {exc}") from exc

        raw = resp.json().get("message", {}).get("content", "")
        return self._parse_response(raw)

    def _parse_response(self, raw: str) -> ClassificationResult:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMProviderError(f"Ollama returned non-JSON: {raw[:200]}") from exc
        return ClassificationResult(
            category=data.get("category", "other"),
            extracted_fields=data.get("extracted_fields", {}),
            model_used=self.model_name,
        )
