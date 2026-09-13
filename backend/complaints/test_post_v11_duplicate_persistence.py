from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from complaints.models import (
    Complaint,
    ComplaintDuplicate,
    ComplaintEmbedding,
)
from complaints.services.complaint_creation_service import (
    detect_and_persist_duplicates,
    persist_duplicate_candidates,
)
from complaints.services.duplicate_detection_service import (
    DuplicateDetectionError,
)
from organizations.models import Category, Department


User = get_user_model()


class DuplicatePersistenceBaseTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(
            name="Water Department",
            is_active=True,
        )

        cls.category = Category.objects.create(
            name="Water Supply",
            department=cls.department,
            is_active=True,
        )

        cls.user = User.objects.create_user(
            email="citizen.persistence@example.com",
            password="TestPass123!",
            role=User.Role.USER,
        )

    def create_complaint(self, title, description):
        return Complaint.objects.create(
            user=self.user,
            category=self.category,
            title=title,
            description=description,
            status=Complaint.Status.SUBMITTED,
        )


class ComplaintDuplicateModelTests(DuplicatePersistenceBaseTestCase):

    def test_duplicate_record_is_created(self):
        complaint = self.create_complaint(
            "Water leakage",
            "There is a major water leakage near the main road.",
        )

        possible_duplicate = self.create_complaint(
            "Water pipe leakage",
            "A water pipe is leaking near the main road.",
        )

        duplicate = ComplaintDuplicate.objects.create(
            complaint=complaint,
            possible_duplicate=possible_duplicate,
            similarity_score=Decimal("0.91234"),
            detection_threshold=Decimal("0.85000"),
            embedding_model="gemini-embedding-001",
        )

        self.assertEqual(
            duplicate.status,
            ComplaintDuplicate.Status.PENDING,
        )

        self.assertEqual(
            duplicate.similarity_score,
            Decimal("0.91234"),
        )

    def test_duplicate_pair_must_be_unique(self):
        complaint = self.create_complaint(
            "Street water leak",
            "Water is leaking continuously from a pipe.",
        )

        possible_duplicate = self.create_complaint(
            "Pipeline leakage",
            "A pipeline is leaking continuously.",
        )

        ComplaintDuplicate.objects.create(
            complaint=complaint,
            possible_duplicate=possible_duplicate,
            similarity_score=Decimal("0.90000"),
            detection_threshold=Decimal("0.85000"),
            embedding_model="gemini-embedding-001",
        )

        with self.assertRaises(Exception):
            ComplaintDuplicate.objects.create(
                complaint=complaint,
                possible_duplicate=possible_duplicate,
                similarity_score=Decimal("0.91000"),
                detection_threshold=Decimal("0.85000"),
                embedding_model="gemini-embedding-001",
            )

    def test_complaint_cannot_be_duplicate_of_itself(self):
        complaint = self.create_complaint(
            "Water complaint",
            "There is a water problem in my street.",
        )

        with self.assertRaises(Exception):
            ComplaintDuplicate.objects.create(
                complaint=complaint,
                possible_duplicate=complaint,
                similarity_score=Decimal("1.00000"),
                detection_threshold=Decimal("0.85000"),
                embedding_model="gemini-embedding-001",
            )


class DuplicatePersistenceServiceTests(
    DuplicatePersistenceBaseTestCase
):

    def test_persist_duplicate_candidates_creates_records(self):
        complaint = self.create_complaint(
            "Water leakage near school",
            "Water is leaking continuously near the school.",
        )

        possible_duplicate = self.create_complaint(
            "Leakage near school",
            "A water pipeline is leaking near the school.",
        )

        ComplaintEmbedding.objects.create(
            complaint=complaint,
            embedding=[0.1] * 768,
            embedding_model="gemini-embedding-001",
            source_text_hash="a" * 64,
        )

        class FakeDetector:
            similarity_threshold = 0.85

        results = [
            {
                "complaint": possible_duplicate,
                "similarity_score": 0.92345,
                "cosine_distance": 0.07655,
            }
        ]

        persisted = persist_duplicate_candidates(
            complaint=complaint,
            duplicate_results=results,
            detector=FakeDetector(),
        )

        self.assertIsNone(persisted)

        duplicate = ComplaintDuplicate.objects.get(
            complaint=complaint,
            possible_duplicate=possible_duplicate,
        )

        self.assertEqual(
            duplicate.similarity_score,
            Decimal("0.92345"),
        )

        self.assertEqual(
            duplicate.detection_threshold,
            Decimal("0.85000"),
        )

        self.assertEqual(
            duplicate.embedding_model,
            "gemini-embedding-001",
        )

        self.assertEqual(
            duplicate.status,
            ComplaintDuplicate.Status.PENDING,
        )

    def test_repeated_detection_does_not_create_duplicate_rows(self):
        complaint = self.create_complaint(
            "Street flooding",
            "Water is collecting on the street after rainfall.",
        )

        possible_duplicate = self.create_complaint(
            "Road water accumulation",
            "There is water accumulation on the same street.",
        )

        ComplaintEmbedding.objects.create(
            complaint=complaint,
            embedding=[0.1] * 768,
            embedding_model="gemini-embedding-001",
            source_text_hash="b" * 64,
        )

        class FakeDetector:
            similarity_threshold = 0.85

        results = [
            {
                "complaint": possible_duplicate,
                "similarity_score": 0.90123,
                "cosine_distance": 0.09877,
            }
        ]

        persist_duplicate_candidates(
            complaint=complaint,
            duplicate_results=results,
            detector=FakeDetector(),
        )

        persist_duplicate_candidates(
            complaint=complaint,
            duplicate_results=results,
            detector=FakeDetector(),
        )

        self.assertEqual(
            ComplaintDuplicate.objects.filter(
                complaint=complaint,
                possible_duplicate=possible_duplicate,
            ).count(),
            1,
        )

    def test_confirmed_review_is_not_overwritten(self):
        complaint = self.create_complaint(
            "Water shortage",
            "No water supply has been available since morning.",
        )

        possible_duplicate = self.create_complaint(
            "Water supply problem",
            "The same locality has no water supply.",
        )

        ComplaintEmbedding.objects.create(
            complaint=complaint,
            embedding=[0.1] * 768,
            embedding_model="gemini-embedding-001",
            source_text_hash="c" * 64,
        )

        duplicate = ComplaintDuplicate.objects.create(
            complaint=complaint,
            possible_duplicate=possible_duplicate,
            similarity_score=Decimal("0.90000"),
            detection_threshold=Decimal("0.85000"),
            embedding_model="gemini-embedding-001",
            status=ComplaintDuplicate.Status.CONFIRMED,
        )

        class FakeDetector:
            similarity_threshold = 0.85

        results = [
            {
                "complaint": possible_duplicate,
                "similarity_score": 0.95000,
                "cosine_distance": 0.05000,
            }
        ]

        persist_duplicate_candidates(
            complaint=complaint,
            duplicate_results=results,
            detector=FakeDetector(),
        )

        duplicate.refresh_from_db()

        self.assertEqual(
            duplicate.status,
            ComplaintDuplicate.Status.CONFIRMED,
        )

        self.assertEqual(
            duplicate.similarity_score,
            Decimal("0.90000"),
        )

    def test_rejected_review_is_not_overwritten(self):
        complaint = self.create_complaint(
            "Broken streetlight",
            "The streetlight is not working outside the building.",
        )

        possible_duplicate = self.create_complaint(
            "Street light issue",
            "The street light is not functioning.",
        )

        ComplaintEmbedding.objects.create(
            complaint=complaint,
            embedding=[0.1] * 768,
            embedding_model="gemini-embedding-001",
            source_text_hash="d" * 64,
        )

        duplicate = ComplaintDuplicate.objects.create(
            complaint=complaint,
            possible_duplicate=possible_duplicate,
            similarity_score=Decimal("0.88000"),
            detection_threshold=Decimal("0.85000"),
            embedding_model="gemini-embedding-001",
            status=ComplaintDuplicate.Status.REJECTED,
        )

        class FakeDetector:
            similarity_threshold = 0.85

        results = [
            {
                "complaint": possible_duplicate,
                "similarity_score": 0.94000,
                "cosine_distance": 0.06000,
            }
        ]

        persist_duplicate_candidates(
            complaint=complaint,
            duplicate_results=results,
            detector=FakeDetector(),
        )

        duplicate.refresh_from_db()

        self.assertEqual(
            duplicate.status,
            ComplaintDuplicate.Status.REJECTED,
        )

        self.assertEqual(
            duplicate.similarity_score,
            Decimal("0.88000"),
        )

    @patch(
        "complaints.services.complaint_creation_service."
        "SemanticDuplicateDetector"
    )
    def test_detection_failure_is_non_blocking(
        self,
        mock_detector,
    ):
        complaint = self.create_complaint(
            "Water problem",
            "There is a serious water problem in the area.",
        )

        mock_detector.return_value.find_similar_complaints.side_effect = (
            DuplicateDetectionError(
                "Embedding provider unavailable."
            )
        )

        results = detect_and_persist_duplicates(complaint)

        self.assertEqual(results, [])

        self.assertEqual(
            ComplaintDuplicate.objects.filter(
                complaint=complaint
            ).count(),
            0,
        )