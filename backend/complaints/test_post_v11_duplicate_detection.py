from unittest.mock import patch

from django.test import TestCase

from accounts.models import User
from complaints.models import Complaint, ComplaintEmbedding
from complaints.services.duplicate_detection_service import (
    DuplicateDetectionError,
    SemanticDuplicateDetector,
    find_possible_duplicates,
)
from organizations.models import Category, Department


class SemanticDuplicateDetectionTests(TestCase):

    def setUp(self):
        self.department = Department.objects.create(
            name="Sanitation",
            description="Sanitation department",
            is_active=True,
        )

        self.category = Category.objects.create(
            name="Garbage Collection",
            description="Garbage collection complaints",
            department=self.department,
            is_active=True,
        )

        self.user = User.objects.create_user(
            email="citizen.duplicate@example.com",
            password="TestPassword123!",
            first_name="Duplicate",
            last_name="Citizen",
            role=User.Role.USER,
        )

        self.complaint = Complaint.objects.create(
            user=self.user,
            category=self.category,
            title="Garbage collection missed",
            description=(
                "Garbage has not been collected from our street "
                "for several days."
            ),
            status=Complaint.Status.SUBMITTED,
            priority=Complaint.Priority.MEDIUM,
            location="Hyderabad",
        )

        self.similar_complaint = Complaint.objects.create(
            user=self.user,
            category=self.category,
            title="Garbage truck not visiting",
            description=(
                "The garbage vehicle has not come to our road "
                "for almost a week."
            ),
            status=Complaint.Status.SUBMITTED,
            priority=Complaint.Priority.MEDIUM,
            location="Hyderabad",
        )

        self.unrelated_complaint = Complaint.objects.create(
            user=self.user,
            category=self.category,
            title="Street light issue",
            description=(
                "The street light near our house has stopped working."
            ),
            status=Complaint.Status.SUBMITTED,
            priority=Complaint.Priority.LOW,
            location="Hyderabad",
        )

    @patch(
        "complaints.services.duplicate_detection_service."
        "create_or_update_complaint_embedding"
    )
    def test_find_similar_complaints_returns_high_similarity_match(
        self,
        mock_create_embedding,
    ):
        current_embedding = ComplaintEmbedding.objects.create(
            complaint=self.complaint,
            embedding=[1.0] + [0.0] * 767,
            embedding_model="test-model",
            source_text_hash="a" * 64,
        )

        mock_create_embedding.return_value = current_embedding

        ComplaintEmbedding.objects.create(
            complaint=self.similar_complaint,
            embedding=[1.0] + [0.01] * 767,
            embedding_model="test-model",
            source_text_hash="b" * 64,
        )

        results = SemanticDuplicateDetector(
            similarity_threshold=0.85,
        ).find_similar_complaints(self.complaint)

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["complaint"].id,
            self.similar_complaint.id,
        )
        self.assertGreaterEqual(
            results[0]["similarity_score"],
            0.85,
        )

    @patch(
        "complaints.services.duplicate_detection_service."
        "create_or_update_complaint_embedding"
    )
    def test_original_complaint_is_excluded(
        self,
        mock_create_embedding,
    ):
        current_embedding = ComplaintEmbedding.objects.create(
            complaint=self.complaint,
            embedding=[1.0] + [0.0] * 767,
            embedding_model="test-model",
            source_text_hash="a" * 64,
        )

        mock_create_embedding.return_value = current_embedding

        ComplaintEmbedding.objects.create(
            complaint=self.similar_complaint,
            embedding=[1.0] + [0.01] * 767,
            embedding_model="test-model",
            source_text_hash="b" * 64,
        )

        results = SemanticDuplicateDetector(
            similarity_threshold=0.85,
        ).find_similar_complaints(self.complaint)

        complaint_ids = [
            result["complaint"].id
            for result in results
        ]

        self.assertNotIn(
            self.complaint.id,
            complaint_ids,
        )

    @patch(
        "complaints.services.duplicate_detection_service."
        "create_or_update_complaint_embedding"
    )
    def test_low_similarity_candidate_is_filtered(
        self,
        mock_create_embedding,
    ):
        current_embedding = ComplaintEmbedding.objects.create(
            complaint=self.complaint,
            embedding=[1.0] + [0.0] * 767,
            embedding_model="test-model",
            source_text_hash="a" * 64,
        )

        mock_create_embedding.return_value = current_embedding

        ComplaintEmbedding.objects.create(
            complaint=self.similar_complaint,
            embedding=[0.0, 1.0] + [0.0] * 766,
            embedding_model="test-model",
            source_text_hash="b" * 64,
        )

        results = SemanticDuplicateDetector(
            similarity_threshold=0.85,
        ).find_similar_complaints(self.complaint)

        self.assertEqual(results, [])

    @patch(
        "complaints.services.duplicate_detection_service."
        "create_or_update_complaint_embedding"
    )
    def test_results_are_ordered_by_similarity(
        self,
        mock_create_embedding,
    ):
        current_embedding = ComplaintEmbedding.objects.create(
            complaint=self.complaint,
            embedding=[1.0] + [0.0] * 767,
            embedding_model="test-model",
            source_text_hash="a" * 64,
        )

        mock_create_embedding.return_value = current_embedding

        ComplaintEmbedding.objects.create(
            complaint=self.similar_complaint,
            embedding=[1.0] + [0.01] * 767,
            embedding_model="test-model",
            source_text_hash="b" * 64,
        )

        ComplaintEmbedding.objects.create(
            complaint=self.unrelated_complaint,
            embedding=[1.0] + [0.1] * 767,
            embedding_model="test-model",
            source_text_hash="c" * 64,
        )

        results = SemanticDuplicateDetector(
            similarity_threshold=0.85,
            max_results=5,
        ).find_similar_complaints(self.complaint)

        self.assertGreaterEqual(len(results), 1)

        scores = [
            result["similarity_score"]
            for result in results
        ]

        self.assertEqual(
            scores,
            sorted(scores, reverse=True),
        )

    @patch(
        "complaints.services.duplicate_detection_service."
        "create_or_update_complaint_embedding"
    )
    def test_same_department_candidates_are_preferred(
        self,
        mock_create_embedding,
    ):
        current_embedding = ComplaintEmbedding.objects.create(
            complaint=self.complaint,
            embedding=[1.0] + [0.0] * 767,
            embedding_model="test-model",
            source_text_hash="a" * 64,
        )

        mock_create_embedding.return_value = current_embedding

        other_department = Department.objects.create(
            name="Water Supply",
            description="Water supply department",
            is_active=True,
        )

        other_category = Category.objects.create(
            name="Water Leakage",
            description="Water leakage complaints",
            department=other_department,
            is_active=True,
        )

        other_complaint = Complaint.objects.create(
            user=self.user,
            category=other_category,
            title="Water leakage",
            description="Water is leaking from a pipe.",
            status=Complaint.Status.SUBMITTED,
            priority=Complaint.Priority.MEDIUM,
            location="Hyderabad",
        )

        ComplaintEmbedding.objects.create(
            complaint=self.similar_complaint,
            embedding=[1.0] + [0.01] * 767,
            embedding_model="test-model",
            source_text_hash="b" * 64,
        )

        ComplaintEmbedding.objects.create(
            complaint=other_complaint,
            embedding=[1.0] + [0.01] * 767,
            embedding_model="test-model",
            source_text_hash="c" * 64,
        )

        results = SemanticDuplicateDetector(
            similarity_threshold=0.85,
        ).find_similar_complaints(self.complaint)

        result_ids = [
            result["complaint"].id
            for result in results
        ]

        self.assertIn(
            self.similar_complaint.id,
            result_ids,
        )
        self.assertNotIn(
            other_complaint.id,
            result_ids,
        )

    def test_invalid_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            SemanticDuplicateDetector(
                similarity_threshold=0,
            )

        with self.assertRaises(ValueError):
            SemanticDuplicateDetector(
                similarity_threshold=1.1,
            )

    def test_invalid_max_results_is_rejected(self):
        with self.assertRaises(ValueError):
            SemanticDuplicateDetector(
                max_results=0,
            )

    def test_invalid_lookback_days_is_rejected(self):
        with self.assertRaises(ValueError):
            SemanticDuplicateDetector(
                lookback_days=0,
            )

    def test_non_complaint_input_is_rejected(self):
        with self.assertRaises(DuplicateDetectionError):
            SemanticDuplicateDetector().find_similar_complaints(
                object()
            )

    @patch(
        "complaints.services.duplicate_detection_service."
        "create_or_update_complaint_embedding"
    )
    def test_embedding_failure_is_wrapped(
        self,
        mock_create_embedding,
    ):
        mock_create_embedding.side_effect = Exception(
            "Embedding service unavailable"
        )

        with self.assertRaises(DuplicateDetectionError):
            SemanticDuplicateDetector().find_similar_complaints(
                self.complaint
            )

    @patch(
        "complaints.services.duplicate_detection_service."
        "create_or_update_complaint_embedding"
    )
    def test_convenience_function_uses_detector(
        self,
        mock_create_embedding,
    ):
        current_embedding = ComplaintEmbedding.objects.create(
            complaint=self.complaint,
            embedding=[1.0] + [0.0] * 767,
            embedding_model="test-model",
            source_text_hash="a" * 64,
        )

        mock_create_embedding.return_value = current_embedding

        ComplaintEmbedding.objects.create(
            complaint=self.similar_complaint,
            embedding=[1.0] + [0.01] * 767,
            embedding_model="test-model",
            source_text_hash="b" * 64,
        )

        results = find_possible_duplicates(
            self.complaint,
            similarity_threshold=0.85,
        )

        self.assertEqual(len(results), 1)