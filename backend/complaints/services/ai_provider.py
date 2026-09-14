import time

from django.conf import settings
from google import genai
from google.genai import types


class AIProviderError(Exception):
    """
    Raised when an AI provider cannot complete a request.
    """

    pass


class AIProvider:
    """
    Base interface for CivicResolve AI providers.
    """

    model_name = "CivicResolve-AI-Base-v1"

    def analyze_complaint(self, prompt):
        """
        Analyze a complaint using the AI provider.
        """
        raise NotImplementedError(
            "AI providers must implement analyze_complaint()."
        )


class GeminiProvider(AIProvider):
    """
    Gemini implementation of the CivicResolve AI provider.

    Uses a small fallback chain so temporary model unavailability
    does not unnecessarily break complaint processing.
    """

    PRIMARY_MODEL = "gemini-3.8-flash"

    FALLBACK_MODELS = (
        "gemini-3.7-flash",
        "gemini-3.5-flash-lite",
    )

    MAX_ATTEMPTS_PER_MODEL = 2
    RETRY_DELAY_SECONDS = 2

    model_name = PRIMARY_MODEL

    def __init__(self):
        api_key = settings.GEMINI_API_KEY

        if not api_key:
            raise AIProviderError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=api_key
        )

    @staticmethod
    def _is_retryable_error(exc):
        """
        Return True for temporary provider/service failures.
        """
        message = str(exc).lower()

        retryable_markers = (
            "503",
            "unavailable",
            "429",
            "resource_exhausted",
            "500",
            "502",
            "504",
            "internal",
            "deadline",
            "temporarily",
        )

        return any(
            marker in message
            for marker in retryable_markers
        )

    def _generate_content(self, model, prompt):
        """
        Send one request to Gemini using the supplied model.
        """
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        if not response.text:
            raise AIProviderError(
                f"Gemini returned an empty response "
                f"from model '{model}'."
            )

        return response.text

    def analyze_complaint(self, prompt):
        """
        Analyze a complaint using Gemini with retry and
        model fallback handling.
        """
        models = (
            self.PRIMARY_MODEL,
            *self.FALLBACK_MODELS,
        )

        errors = []

        for model in models:
            for attempt in range(
                1,
                self.MAX_ATTEMPTS_PER_MODEL + 1,
            ):
                try:
                    response_text = self._generate_content(
                        model,
                        prompt,
                    )

                    self.model_name = model

                    return response_text

                except AIProviderError as exc:
                    errors.append(
                        f"{model} attempt {attempt}: {exc}"
                    )

                    if not self._is_retryable_error(exc):
                        raise

                except Exception as exc:
                    wrapped_error = AIProviderError(
                        f"Gemini request failed for "
                        f"model '{model}': {exc}"
                    )

                    errors.append(
                        f"{model} attempt {attempt}: "
                        f"{wrapped_error}"
                    )

                    if not self._is_retryable_error(exc):
                        raise wrapped_error from exc

                if attempt < self.MAX_ATTEMPTS_PER_MODEL:
                    time.sleep(
                        self.RETRY_DELAY_SECONDS
                    )

        raise AIProviderError(
            "All configured Gemini models failed. "
            + " | ".join(errors)
        )


class PlaceholderAIProvider(AIProvider):
    """
    Temporary provider used for backend development
    and automated testing.

    This provider does not call an external AI service.
    """

    model_name = "CivicResolve-AI-Placeholder-v1"

    def analyze_complaint(self, prompt):
        """
        Return a predictable response for testing.
        """
        return {
            "summary": (
                "AI analysis is currently using the "
                "CivicResolve placeholder provider."
            ),
            "predicted_category": None,
            "predicted_department": None,
            "predicted_priority": "MEDIUM",
            "urgency_score": 50,
            "confidence_score": 0,
        }