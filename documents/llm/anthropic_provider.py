"""
Anthropic Claude provider implementation.
Uses the official `anthropic` SDK.
"""
import json
from django.conf import settings
import anthropic

from .base import BaseLLMProvider, ClassificationResult, LLMProviderError
from .prompts import SYSTEM_PROMPT, build_user_message

_MODEL = "claude-sonnet-4-20250514"


class AnthropicProvider(BaseLLMProvider):
    """Calls Anthropic's Claude API for classification and extraction."""

    def __init__(self):
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            raise LLMProviderError(
                "ANTHROPIC_API_KEY is not set. "
                "Add it to your .env file or set LLM_PROVIDER=ollama for local mode."
            )
        self._client = anthropic.Anthropic(
            api_key=api_key,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )

    @property
    def model_name(self) -> str:
        return _MODEL

    def classify_and_extract(self, text: str, filename: str) -> ClassificationResult:
        user_message = build_user_message(text, filename)
        try:
            response = self._client.messages.create(
                model=_MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
        except anthropic.APIConnectionError as exc:
            raise LLMProviderError(f"Cannot reach Anthropic API: {exc}") from exc
        except anthropic.APIStatusError as exc:
            raise LLMProviderError(
                f"Anthropic API error {exc.status_code}: {exc.message}"
            ) from exc

        raw = response.content[0].text.strip()
        return self._parse_response(raw)

    def _parse_response(self, raw: str) -> ClassificationResult:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMProviderError(
                f"LLM returned non-JSON response: {raw[:200]}"
            ) from exc

        category = data.get("category", "other")
        extracted_fields = data.get("extracted_fields", {})
        return ClassificationResult(
            category=category,
            extracted_fields=extracted_fields,
            model_used=_MODEL,
        )
