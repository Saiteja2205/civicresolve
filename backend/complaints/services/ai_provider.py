class AIProviderError(Exception):
    """
    Raised when the AI provider cannot generate a valid response.
    """

    pass


class AIProvider:
    """
    Base interface for CivicResolve AI providers.
    """

    model_name = "CivicResolve-AI-Placeholder-v1"

    def analyze_complaint(self, prompt):
        """
        Analyze a complaint using the configured AI provider.

        This method will be implemented when we connect
        the actual AI provider.
        """

        raise NotImplementedError(
            "AI provider has not been connected yet."
        )


class PlaceholderAIProvider(AIProvider):
    """
    Temporary provider used for backend development and testing.

    This does NOT call an external AI service.
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