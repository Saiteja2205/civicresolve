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
    """

    model_name = "gemini-3.8-flash"

    def __init__(self):
        api_key = settings.GEMINI_API_KEY

        if not api_key:
            raise AIProviderError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=api_key
        )

    def analyze_complaint(self, prompt):
        """
        Send a complaint-analysis prompt to Gemini
        and return the generated JSON text.
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )

            if not response.text:
                raise AIProviderError(
                    "Gemini returned an empty response."
                )

            return response.text

        except AIProviderError:
            raise

        except Exception as exc:
            raise AIProviderError(
                f"Gemini request failed: {exc}"
            ) from exc


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