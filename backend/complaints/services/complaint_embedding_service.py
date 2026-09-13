import hashlib

from complaints.models import Complaint, ComplaintEmbedding
from complaints.services.embedding_provider import (
    EmbeddingProviderError,
    GeminiEmbeddingProvider,
)


def build_complaint_embedding_text(complaint):
    """
    Build the canonical text representation used for semantic embeddings.
    """

    if not isinstance(complaint, Complaint):
        raise ValueError("Expected a Complaint instance.")

    category_name = ""
    department_name = ""

    if complaint.category_id:
        category_name = complaint.category.name

        if complaint.category.department_id:
            department_name = complaint.category.department.name

    parts = [
        f"Title: {complaint.title.strip()}",
        f"Description: {complaint.description.strip()}",
    ]

    if category_name:
        parts.append(f"Category: {category_name}")

    if department_name:
        parts.append(f"Department: {department_name}")

    if complaint.location:
        parts.append(f"Location: {complaint.location.strip()}")

    return "\n".join(parts)


def calculate_source_text_hash(text):
    """
    Calculate a deterministic SHA-256 hash for the canonical text.
    """

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def create_or_update_complaint_embedding(complaint):
    """
    Generate and persist the semantic embedding for a complaint.

    If an embedding already exists, it is updated only when the canonical
    source text has changed.
    """

    canonical_text = build_complaint_embedding_text(complaint)
    source_text_hash = calculate_source_text_hash(canonical_text)

    existing_embedding = ComplaintEmbedding.objects.filter(
        complaint=complaint
    ).first()

    if (
        existing_embedding is not None
        and existing_embedding.source_text_hash == source_text_hash
    ):
        return existing_embedding

    provider = GeminiEmbeddingProvider()
    embedding_values = provider.embed_text(canonical_text)

    embedding, _ = ComplaintEmbedding.objects.update_or_create(
        complaint=complaint,
        defaults={
            "embedding": embedding_values,
            "embedding_model": provider.MODEL_NAME,
            "source_text_hash": source_text_hash,
        },
    )

    return embedding