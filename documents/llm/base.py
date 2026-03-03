"""
Abstract base class for LLM providers.
All concrete providers must implement `classify_and_extract`.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ClassificationResult:
    category: str
    extracted_fields: dict
    model_used: str


class BaseLLMProvider(ABC):
    """Strategy interface for LLM-based document classification."""

    @abstractmethod
    def classify_and_extract(self, text: str, filename: str) -> ClassificationResult:
        """
        Given raw document text and original filename, return:
          - category (one of the defined DocumentCategory values)
          - extracted_fields (dict keyed by field name)
          - model_used (model identifier string)

        Must raise LLMProviderError on any unrecoverable failure.
        """
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model identifier."""
        ...


class LLMProviderError(Exception):
    """Raised when the LLM provider is unreachable or returns an invalid response."""
    pass
