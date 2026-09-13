from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from accounts.models import User
from complaints.models import Complaint, ComplaintEmbedding
from complaints.services.complaint_embedding_service import (
    build_complaint_embedding_text,
    calculate_source_text_hash,
    create_or_update_complaint_embedding,
)
from complaints.services.embedding_provider import (
    EmbeddingProviderError,
    GeminiEmbeddingProvider,
)
from organizations.models import Category, Department


class ComplaintEmbeddingServiceTests(TestCase):

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
            email="citizen.embedding@example.com",
            password="TestPassword123!",
            first_name="Embedding",
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

    def test_build_canonical_complaint_text(self):
        text = build_complaint_embedding_text(self.complaint)

        self.assertIn(
            "Title: Garbage collection missed",
            text,
        )
        self.assertIn(
            "Garbage has not been collected from our street",
            text,
        )
        self.assertIn(
            "Category: Garbage Collection",
            text,
        )
        self.assertIn(
            "Department: Sanitation",
            text,
        )
        self.assertIn(
            "Location: Hyderabad",
            text,
        )

    def test_source_text_hash_is_deterministic(self):
        text = build_complaint_embedding_text(self.complaint)

        first_hash = calculate_source_text_hash(text)
        second_hash = calculate_source_text_hash(text)

        self.assertEqual(first_hash, second_hash)
        self.assertEqual(len(first_hash), 64)

    def test_source_text_hash_changes_when_text_changes(self):
        first_text = build_complaint_embedding_text(self.complaint)
        first_hash = calculate_source_text_hash(first_text)

        self.complaint.description = (
            "Garbage has not been collected for two weeks."
        )
        self.complaint.save()

        second_text = build_complaint_embedding_text(self.complaint)
        second_hash = calculate_source_text_hash(second_text)

        self.assertNotEqual(first_hash, second_hash)

    @patch(
        "complaints.services.complaint_embedding_service."
        "GeminiEmbeddingProvider.embed_text"
    )
    def test_create_embedding(self, mock_embed_text):
        fake_embedding = [0.01] * 768
        mock_embed_text.return_value = fake_embedding

        embedding = create_or_update_complaint_embedding(
            self.complaint
        )

        self.assertIsNotNone(embedding)
        self.assertEqual(
            embedding.complaint_id,
            self.complaint.id,
        )
        self.assertEqual(
            embedding.embedding_model,
            GeminiEmbeddingProvider.MODEL_NAME,
        )
        self.assertEqual(
            len(embedding.embedding),
            768,
        )
        self.assertEqual(
            embedding.source_text_hash,
            calculate_source_text_hash(
                build_complaint_embedding_text(self.complaint)
            ),
        )

        mock_embed_text.assert_called_once()

    @patch(
        "complaints.services.complaint_embedding_service."
        "GeminiEmbeddingProvider.embed_text"
    )
    def test_existing_unchanged_embedding_is_reused(
        self,
        mock_embed_text,
    ):
        fake_embedding = [0.01] * 768
        mock_embed_text.return_value = fake_embedding

        first_embedding = create_or_update_complaint_embedding(
            self.complaint
        )

        mock_embed_text.reset_mock()

        second_embedding = create_or_update_complaint_embedding(
            self.complaint
        )

        self.assertEqual(
            first_embedding.id,
            second_embedding.id,
        )
        mock_embed_text.assert_not_called()

    @patch(
        "complaints.services.complaint_embedding_service."
        "GeminiEmbeddingProvider.embed_text"
    )
    def test_changed_complaint_regenerates_embedding(
        self,
        mock_embed_text,
    ):
        fake_embedding = [0.01] * 768
        mock_embed_text.return_value = fake_embedding

        first_embedding = create_or_update_complaint_embedding(
            self.complaint
        )

        self.complaint.description = (
            "Garbage has not been collected for two weeks."
        )
        self.complaint.save()

        mock_embed_text.reset_mock()

        second_embedding = create_or_update_complaint_embedding(
            self.complaint
        )

        self.assertEqual(
            first_embedding.id,
            second_embedding.id,
        )
        mock_embed_text.assert_called_once()

        self.assertNotEqual(
            first_embedding.source_text_hash,
            second_embedding.source_text_hash,
        )

    @patch(
        "complaints.services.embedding_provider."
        "genai.Client"
    )
    def test_provider_rejects_empty_text(self, mock_client):
        provider = GeminiEmbeddingProvider()

        with self.assertRaises(EmbeddingProviderError):
            provider.embed_text("")

        mock_client.assert_called_once()

    @patch(
        "complaints.services.embedding_provider."
        "genai.Client"
    )
    def test_provider_rejects_wrong_embedding_dimension(
        self,
        mock_client,
    ):
        mock_response = type(
            "Response",
            (),
            {
                "embeddings": [
                    type(
                        "Embedding",
                        (),
                        {
                            "values": [0.01] * 10,
                        },
                    )()
                ]
            },
        )()

        mock_client.return_value.models.embed_content.return_value = (
            mock_response
        )

        provider = GeminiEmbeddingProvider()

        with self.assertRaises(EmbeddingProviderError):
            provider.embed_text("test complaint")