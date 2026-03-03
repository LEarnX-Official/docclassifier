"""
OpenAI provider implementation.
"""
import json
from django.conf import settings
from openai import OpenAI, APIConnectionError, APIStatusError

from .base import BaseLLMProvider, ClassificationResult, LLMProviderError
from .prompts import SYSTEM_PROMPT, build_user_message

_MODEL = "gpt-4o-mini"


class OpenAIProvider(BaseLLMProvider):
    """Calls the OpenAI Chat Completions API."""

    def __init__(self):
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise LLMProviderError(
                "OPENAI_API_KEY is not set. Add it to .env or choose a different provider."
            )
        self._client = OpenAI(
            api_key=api_key,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )

    @property
    def model_name(self) -> str:
        return _MODEL

    def classify_and_extract(self, text: str, filename: str) -> ClassificationResult:
        user_message = build_user_message(text, filename)
        try:
            response = self._client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=1024,
                response_format={"type": "json_object"},
            )
        except APIConnectionError as exc:
            raise LLMProviderError(f"Cannot reach OpenAI API: {exc}") from exc
        except APIStatusError as exc:
            raise LLMProviderError(
                f"OpenAI API error {exc.status_code}: {exc.message}"
            ) from exc

        raw = response.choices[0].message.content.strip()
        return self._parse_response(raw)

    def _parse_response(self, raw: str) -> ClassificationResult:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMProviderError(f"LLM returned non-JSON: {raw[:200]}") from exc
        return ClassificationResult(
            category=data.get("category", "other"),
            extracted_fields=data.get("extracted_fields", {}),
            model_used=_MODEL,
        )
