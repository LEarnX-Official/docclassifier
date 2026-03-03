"""
Tests for LLM provider implementations.
Uses mocks — no real API calls are made.
"""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from documents.llm.base import LLMProviderError
from documents.llm.openai_provider import OpenAIProvider
from documents.llm.ollama_provider import OllamaProvider
from documents.llm.factory import get_llm_provider


VALID_RESPONSE = json.dumps({
    "category": "invoice",
    "extracted_fields": {
        "issuer": "ACME SRL",
        "recipient": "Beta Corp",
        "invoice_number": "INV-2026-001",
        "invoice_date": "2026-03-01",
        "total_amount": "1180.00 EUR",
        "vat_amount": "180.00 EUR",
    }
})


class OpenAIProviderTests(TestCase):

    @override_settings(OPENAI_API_KEY="test-key", LLM_TIMEOUT_SECONDS=10)
    def test_successful_classification(self):
        mock_choice = MagicMock()
        mock_choice.message.content = VALID_RESPONSE
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        with patch("documents.llm.openai_provider.OpenAI") as MockClient:
            MockClient.return_value.chat.completions.create.return_value = mock_response
            provider = OpenAIProvider()
            result = provider.classify_and_extract("Invoice text here", "fattura.pdf")
        self.assertEqual(result.category, "invoice")
        self.assertEqual(result.extracted_fields["issuer"], "ACME SRL")

    @override_settings(OPENAI_API_KEY="test-key", LLM_TIMEOUT_SECONDS=10)
    def test_connection_error_raises_llm_error(self):
        from openai import APIConnectionError
        with patch("documents.llm.openai_provider.OpenAI") as MockClient:
            MockClient.return_value.chat.completions.create.side_effect = (
                APIConnectionError(request=MagicMock())
            )
            provider = OpenAIProvider()
            with self.assertRaises(LLMProviderError):
                provider.classify_and_extract("text", "doc.pdf")

    @override_settings(OPENAI_API_KEY="", LLM_TIMEOUT_SECONDS=10)
    def test_missing_api_key_raises_llm_error(self):
        with self.assertRaises(LLMProviderError):
            OpenAIProvider()

    @override_settings(OPENAI_API_KEY="test-key", LLM_TIMEOUT_SECONDS=10)
    def test_invalid_json_raises_llm_error(self):
        mock_choice = MagicMock()
        mock_choice.message.content = "not valid json {{"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        with patch("documents.llm.openai_provider.OpenAI") as MockClient:
            MockClient.return_value.chat.completions.create.return_value = mock_response
            provider = OpenAIProvider()
            with self.assertRaises(LLMProviderError):
                provider.classify_and_extract("text", "doc.pdf")


class OllamaProviderTests(TestCase):

    @override_settings(
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_MODEL="llama3.2",
        LLM_TIMEOUT_SECONDS=10,
    )
    def test_successful_classification(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"message": {"content": VALID_RESPONSE}}
        mock_resp.raise_for_status = MagicMock()
        with patch("documents.llm.ollama_provider.requests.post", return_value=mock_resp):
            provider = OllamaProvider()
            result = provider.classify_and_extract("Invoice text", "fattura.pdf")
        self.assertEqual(result.category, "invoice")

    @override_settings(
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_MODEL="llama3.2",
        LLM_TIMEOUT_SECONDS=10,
    )
    def test_connection_error_raises_llm_error(self):
        import requests as _requests
        with patch(
            "documents.llm.ollama_provider.requests.post",
            side_effect=_requests.ConnectionError,
        ):
            provider = OllamaProvider()
            with self.assertRaises(LLMProviderError):
                provider.classify_and_extract("text", "doc.pdf")


class FactoryTests(TestCase):

    @override_settings(
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="key",
        LLM_TIMEOUT_SECONDS=10,
    )
    def test_factory_returns_openai(self):
        with patch("documents.llm.openai_provider.OpenAI"):
            provider = get_llm_provider()
        self.assertIsInstance(provider, OpenAIProvider)

    @override_settings(
        LLM_PROVIDER="ollama",
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_MODEL="llama3.2",
        LLM_TIMEOUT_SECONDS=10,
    )
    def test_factory_returns_ollama(self):
        provider = get_llm_provider()
        self.assertIsInstance(provider, OllamaProvider)

    @override_settings(LLM_PROVIDER="anthropic")
    def test_factory_raises_for_unknown_provider(self):
        with self.assertRaises(ValueError):
            get_llm_provider()
