from django.conf import settings
from google import genai
from google.genai import types


class EmbeddingProviderError(Exception):
    """Raised when the embedding provider cannot generate an embedding."""


class GeminiEmbeddingProvider:
    """
    Generates semantic embeddings for CivicResolve complaint text.

    The project stores embeddings as 768-dimensional pgvector vectors.
    """

    MODEL_NAME = "gemini-embedding-001"
    OUTPUT_DIMENSIONALITY = 768

    def __init__(self):
        api_key = getattr(settings, "GEMINI_API_KEY", None)

        if not api_key:
            raise EmbeddingProviderError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(api_key=api_key)

    def embed_text(self, text):
        """
        Generate a single 768-dimensional embedding for the supplied text.
        """

        if not isinstance(text, str) or not text.strip():
            raise EmbeddingProviderError(
                "Embedding text must be a non-empty string."
            )

        try:
            response = self.client.models.embed_content(
                model=self.MODEL_NAME,
                contents=text.strip(),
                config=types.EmbedContentConfig(
                    output_dimensionality=self.OUTPUT_DIMENSIONALITY,
                ),
            )
        except Exception as exc:
            raise EmbeddingProviderError(
                f"Failed to generate complaint embedding: {exc}"
            ) from exc

        embeddings = getattr(response, "embeddings", None)

        if not embeddings:
            raise EmbeddingProviderError(
                "Embedding provider returned no embeddings."
            )

        values = getattr(embeddings[0], "values", None)

        if not values:
            raise EmbeddingProviderError(
                "Embedding provider returned an empty embedding."
            )

        if len(values) != self.OUTPUT_DIMENSIONALITY:
            raise EmbeddingProviderError(
                "Embedding dimension mismatch: "
                f"expected {self.OUTPUT_DIMENSIONALITY}, "
                f"received {len(values)}."
            )

        return list(values)