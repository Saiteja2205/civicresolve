from datetime import timedelta

from django.utils import timezone
from pgvector.django import CosineDistance

from complaints.models import Complaint, ComplaintEmbedding
from complaints.services.complaint_embedding_service import (
    create_or_update_complaint_embedding,
)


class DuplicateDetectionError(Exception):
    """Raised when duplicate detection cannot be completed."""


class SemanticDuplicateDetector:
    """
    Finds semantically similar complaints using pgvector cosine distance.

    Duplicate detection is intentionally advisory. It never rejects,
    deletes, closes, or otherwise changes a complaint.
    """

    DEFAULT_SIMILARITY_THRESHOLD = 0.85
    DEFAULT_MAX_RESULTS = 5
    DEFAULT_LOOKBACK_DAYS = 180

    def __init__(
        self,
        similarity_threshold=DEFAULT_SIMILARITY_THRESHOLD,
        max_results=DEFAULT_MAX_RESULTS,
        lookback_days=DEFAULT_LOOKBACK_DAYS,
    ):
        if not 0 < similarity_threshold <= 1:
            raise ValueError(
                "similarity_threshold must be greater than 0 and at most 1."
            )

        if max_results < 1:
            raise ValueError("max_results must be at least 1.")

        if lookback_days < 1:
            raise ValueError("lookback_days must be at least 1.")

        self.similarity_threshold = similarity_threshold
        self.max_results = max_results
        self.lookback_days = lookback_days

    def find_similar_complaints(self, complaint):
        """
        Find existing complaints that are semantically similar.

        The supplied complaint is excluded from its own candidate results.
        Candidates are limited to a configurable lookback period and,
        when possible, the same department.
        """

        if not isinstance(complaint, Complaint):
            raise DuplicateDetectionError(
                "Expected a Complaint instance."
            )

        try:
            embedding = create_or_update_complaint_embedding(complaint)
        except Exception as exc:
            raise DuplicateDetectionError(
                f"Unable to prepare complaint embedding: {exc}"
            ) from exc

        cutoff_time = timezone.now() - timedelta(
            days=self.lookback_days
        )

        candidates = (
            ComplaintEmbedding.objects
            .filter(
                complaint__created_at__gte=cutoff_time,
            )
            .exclude(
                complaint_id=complaint.id,
            )
            .select_related(
                "complaint",
                "complaint__category",
                "complaint__category__department",
            )
        )

        # Prefer candidates from the same department when the complaint
        # already has a category/department. If no same-department
        # candidates exist, fall back to all recent candidates.
        if (
            complaint.category_id
            and complaint.category.department_id
        ):
            same_department = candidates.filter(
                complaint__category__department_id=(
                    complaint.category.department_id
                )
            )

            if same_department.exists():
                candidates = same_department

        candidates = candidates.annotate(
            cosine_distance=CosineDistance(
                "embedding",
                embedding.embedding,
            )
        ).order_by(
            "cosine_distance",
            "complaint_id",
        )[: self.max_results]

        results = []

        for candidate in candidates:
            similarity = 1 - float(candidate.cosine_distance)

            if similarity < self.similarity_threshold:
                continue

            results.append(
                {
                    "complaint": candidate.complaint,
                    "similarity_score": similarity,
                    "cosine_distance": float(
                        candidate.cosine_distance
                    ),
                }
            )

        return results


def find_possible_duplicates(
    complaint,
    similarity_threshold=SemanticDuplicateDetector.DEFAULT_SIMILARITY_THRESHOLD,
    max_results=SemanticDuplicateDetector.DEFAULT_MAX_RESULTS,
    lookback_days=SemanticDuplicateDetector.DEFAULT_LOOKBACK_DAYS,
):
    """
    Convenience function for semantic duplicate detection.
    """

    detector = SemanticDuplicateDetector(
        similarity_threshold=similarity_threshold,
        max_results=max_results,
        lookback_days=lookback_days,
    )

    return detector.find_similar_complaints(complaint)