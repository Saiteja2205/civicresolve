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

    def analyze_image(self, prompt, image_bytes, mime_type):
        """
        Analyze an image using the AI provider.
        """
        raise NotImplementedError(
            "AI providers must implement analyze_image()."
        )


class GeminiProvider(AIProvider):
    """
    Gemini implementation of the CivicResolve AI provider.

    Supports:
    - Text-based complaint analysis
    - Multimodal image/evidence analysis

    Uses:
    - Request timeout protection
    - Retry handling
    - Model fallback handling
    """

    PRIMARY_MODEL = "gemini-3.8-flash"

    FALLBACK_MODELS = (
        "gemini-3.7-flash",
        "gemini-3.5-flash-lite",
    )

    MAX_ATTEMPTS_PER_MODEL = 2
    RETRY_DELAY_SECONDS = 2

    # Google GenAI SDK expects this value in milliseconds.
    REQUEST_TIMEOUT_MS = 60000

    model_name = PRIMARY_MODEL

    def __init__(self):
        api_key = settings.GEMINI_API_KEY

        if not api_key:
            raise AIProviderError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=self.REQUEST_TIMEOUT_MS,
            ),
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
            "timeout",
            "timed out",
        )

        return any(
            marker in message
            for marker in retryable_markers
        )

    @staticmethod
    def _format_request_error(
        model,
        exc,
    ):
        """
        Convert a low-level Gemini/network exception into
        a useful CivicResolve AIProviderError.
        """

        message = str(exc).strip()

        if not message:
            message = exc.__class__.__name__

        return AIProviderError(
            f"Gemini request failed for model "
            f"'{model}': {message}"
        )

    def _generate_content(
        self,
        model,
        prompt,
    ):
        """
        Send one text request to Gemini.

        The client-level HTTP timeout prevents an individual
        network request from waiting indefinitely.
        """

        try:
            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )

        except Exception as exc:
            raise self._format_request_error(
                model=model,
                exc=exc,
            ) from exc

        if not response.text:
            raise AIProviderError(
                f"Gemini returned an empty response "
                f"from model '{model}'."
            )

        return response.text

    def _generate_image_content(
        self,
        model,
        prompt,
        image_bytes,
        mime_type,
    ):
        """
        Send one multimodal image request to Gemini.
        """

        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type,
        )

        try:
            response = self.client.models.generate_content(
                model=model,
                contents=[
                    prompt,
                    image_part,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )

        except Exception as exc:
            raise AIProviderError(
                f"Gemini image request failed for model "
                f"'{model}': {str(exc)}"
            ) from exc

        if not response.text:
            raise AIProviderError(
                f"Gemini returned an empty image-analysis "
                f"response from model '{model}'."
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
                    response_text = (
                        self._generate_content(
                            model,
                            prompt,
                        )
                    )

                    self.model_name = model

                    return response_text

                except AIProviderError as exc:
                    errors.append(
                        f"{model} attempt {attempt}: "
                        f"{exc}"
                    )

                    if not self._is_retryable_error(
                        exc
                    ):
                        raise

                except Exception as exc:
                    wrapped_error = (
                        self._format_request_error(
                            model=model,
                            exc=exc,
                        )
                    )

                    errors.append(
                        f"{model} attempt {attempt}: "
                        f"{wrapped_error}"
                    )

                    if not self._is_retryable_error(
                        exc
                    ):
                        raise wrapped_error from exc

                if attempt < self.MAX_ATTEMPTS_PER_MODEL:
                    time.sleep(
                        self.RETRY_DELAY_SECONDS
                    )

        raise AIProviderError(
            "All configured Gemini models failed. "
            + " | ".join(errors)
        )

    def analyze_image(
        self,
        prompt,
        image_bytes,
        mime_type,
    ):
        """
        Analyze complaint evidence using Gemini vision
        with retry and model fallback handling.
        """

        if not image_bytes:
            raise AIProviderError(
                "Image data is empty."
            )

        if not mime_type:
            raise AIProviderError(
                "Image MIME type is required."
            )

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
                    response_text = (
                        self._generate_image_content(
                            model=model,
                            prompt=prompt,
                            image_bytes=image_bytes,
                            mime_type=mime_type,
                        )
                    )

                    self.model_name = model

                    return response_text

                except AIProviderError as exc:
                    errors.append(
                        f"{model} image attempt "
                        f"{attempt}: {exc}"
                    )

                    if not self._is_retryable_error(
                        exc
                    ):
                        raise

                except Exception as exc:
                    wrapped_error = (
                        self._format_request_error(
                            model=model,
                            exc=exc,
                        )
                    )

                    errors.append(
                        f"{model} image attempt "
                        f"{attempt}: {wrapped_error}"
                    )

                    if not self._is_retryable_error(
                        exc
                    ):
                        raise wrapped_error from exc

                if attempt < self.MAX_ATTEMPTS_PER_MODEL:
                    time.sleep(
                        self.RETRY_DELAY_SECONDS
                    )

        raise AIProviderError(
            "All configured Gemini models failed for "
            "image analysis. "
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

    def analyze_image(
        self,
        prompt,
        image_bytes,
        mime_type,
    ):
        """
        Return a predictable image-analysis response
        for automated evidence testing.
        """

        return {
            "evidence_type": "OTHER",
            "observations": (
                "Placeholder image analysis."
            ),
            "severity_score": 50,
            "confidence_score": 0,
            "complaint_consistency": True,
            "analysis_explanation": (
                "Placeholder provider response "
                "for evidence testing."
            ),
        }