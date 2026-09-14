from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from complaints.models import (
    Complaint,
    ComplaintAssignment,
)
from organizations.models import Category, Department


User = get_user_model()


class ResolutionAssistantAPITests(
    APITestCase
):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(
            name="Water Supply Department"
        )

        cls.category = Category.objects.create(
            name="Water Leakage",
            department=cls.department,
        )

        cls.other_department = Department.objects.create(
            name="Roads and Infrastructure Department"
        )

        cls.other_category = Category.objects.create(
            name="Road Damage",
            department=cls.other_department,
        )

        cls.citizen = User.objects.create_user(
            email="resolution.citizen@test.local",
            password="TestPass123!",
            role=User.Role.USER,
            is_active=True,
        )

        cls.officer = User.objects.create_user(
            email="resolution.officer@test.local",
            password="TestPass123!",
            role=User.Role.OFFICER,
            is_active=True,
            department=cls.department,
        )

        cls.other_officer = User.objects.create_user(
            email="other.officer@test.local",
            password="TestPass123!",
            role=User.Role.OFFICER,
            is_active=True,
            department=cls.other_department,
        )

        cls.admin = User.objects.create_user(
            email="resolution.admin@test.local",
            password="TestPass123!",
            role=User.Role.ADMIN,
            is_active=True,
        )

        cls.complaint = Complaint.objects.create(
            user=cls.citizen,
            category=cls.category,
            title="Water leakage near Block A",
            description=(
                "There is a continuous water leakage "
                "near Block A since yesterday."
            ),
            priority=Complaint.Priority.MEDIUM,
            status=Complaint.Status.IN_PROGRESS,
        )

        ComplaintAssignment.objects.create(
            complaint=cls.complaint,
            department=cls.department,
            officer=cls.officer,
            assigned_by=cls.admin,
            reason="Test assignment",
        )

        cls.unassigned_complaint = Complaint.objects.create(
            user=cls.citizen,
            category=cls.other_category,
            title="Road damage near Block B",
            description=(
                "A large pothole is causing problems "
                "for vehicles near Block B."
            ),
            priority=Complaint.Priority.HIGH,
            status=Complaint.Status.ASSIGNED,
        )

    def setUp(self):
        self.url = reverse(
            "complaint-resolution-assistant",
            kwargs={
                "complaint_id": self.complaint.id,
            },
        )

    @patch(
        "complaints.services.resolution_assistant_service."
        "GeminiProvider"
    )
    def test_assigned_officer_can_generate_draft(
        self,
        mock_provider,
    ):
        mock_instance = mock_provider.return_value

        mock_instance.model_name = (
            "test-resolution-model"
        )

        mock_instance.analyze_complaint.return_value = """
        {
          "resolution_draft": "Inspect the reported leakage and coordinate the required repair.",
          "recommended_actions": [
            "Inspect the leakage location.",
            "Coordinate the required repair."
          ],
          "citizen_response_draft": "Your complaint has been reviewed. The responsible team should inspect the reported leakage and take the required action.",
          "confidence_score": 88,
          "basis": [
            "Complaint description",
            "Current complaint status"
          ]
        }
        """

        self.client.force_authenticate(
            user=self.officer
        )

        response = self.client.post(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["complaint"],
            self.complaint.id,
        )

        self.assertEqual(
            response.data["ticket_number"],
            self.complaint.ticket_number,
        )

        self.assertEqual(
            response.data["confidence_score"],
            88.0,
        )

        self.assertEqual(
            response.data["model"],
            "test-resolution-model",
        )

        self.assertGreaterEqual(
            len(
                response.data[
                    "recommended_actions"
                ]
            ),
            1,
        )

        mock_instance.analyze_complaint.assert_called_once()

    @patch(
        "complaints.services.resolution_assistant_service."
        "GeminiProvider"
    )
    def test_admin_can_generate_draft(
        self,
        mock_provider,
    ):
        mock_instance = mock_provider.return_value

        mock_instance.model_name = (
            "test-resolution-model"
        )

        mock_instance.analyze_complaint.return_value = """
        {
          "resolution_draft": "Review the complaint and take the appropriate departmental action.",
          "recommended_actions": [
            "Review the complaint.",
            "Take the appropriate departmental action."
          ],
          "citizen_response_draft": "Your complaint is under review by the responsible department.",
          "confidence_score": 80,
          "basis": [
            "Complaint description"
          ]
        }
        """

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_citizen_is_forbidden(self):
        self.client.force_authenticate(
            user=self.citizen
        )

        response = self.client.post(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_unassigned_officer_is_forbidden(self):
        url = reverse(
            "complaint-resolution-assistant",
            kwargs={
                "complaint_id": (
                    self.unassigned_complaint.id
                ),
            },
        )

        self.client.force_authenticate(
            user=self.other_officer
        )

        response = self.client.post(
            url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_unknown_complaint_returns_404(self):
        url = reverse(
            "complaint-resolution-assistant",
            kwargs={
                "complaint_id": 999999,
            },
        )

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    @patch(
        "complaints.services.resolution_assistant_service."
        "GeminiProvider"
    )
    def test_invalid_ai_json_returns_503(
        self,
        mock_provider,
    ):
        mock_instance = mock_provider.return_value

        mock_instance.model_name = (
            "test-resolution-model"
        )

        mock_instance.analyze_complaint.return_value = (
            "not valid json"
        )

        self.client.force_authenticate(
            user=self.officer
        )

        response = self.client.post(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )

        self.assertIn(
            "invalid JSON",
            response.data["detail"],
        )

    @patch(
        "complaints.services.resolution_assistant_service."
        "GeminiProvider"
    )
    def test_missing_required_ai_field_returns_503(
        self,
        mock_provider,
    ):
        mock_instance = mock_provider.return_value

        mock_instance.model_name = (
            "test-resolution-model"
        )

        mock_instance.analyze_complaint.return_value = """
        {
          "resolution_draft": "Review the complaint.",
          "recommended_actions": [
            "Review the complaint."
          ],
          "citizen_response_draft": "Your complaint is under review.",
          "confidence_score": 80
        }
        """

        self.client.force_authenticate(
            user=self.officer
        )

        response = self.client.post(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )

        self.assertIn(
            "missing required fields",
            response.data["detail"],
        )

    @patch(
        "complaints.services.resolution_assistant_service."
        "GeminiProvider"
    )
    def test_invalid_confidence_returns_503(
        self,
        mock_provider,
    ):
        mock_instance = mock_provider.return_value

        mock_instance.model_name = (
            "test-resolution-model"
        )

        mock_instance.analyze_complaint.return_value = """
        {
          "resolution_draft": "Review the complaint.",
          "recommended_actions": [
            "Review the complaint."
          ],
          "citizen_response_draft": "Your complaint is under review.",
          "confidence_score": 150,
          "basis": [
            "Complaint description"
          ]
        }
        """

        self.client.force_authenticate(
            user=self.officer
        )

        response = self.client.post(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )

        self.assertIn(
            "between 0 and 100",
            response.data["detail"],
        )

    @patch(
        "complaints.services.resolution_assistant_service."
        "GeminiProvider"
    )
    def test_provider_failure_returns_503(
        self,
        mock_provider,
    ):
        from complaints.services.ai_provider import (
            AIProviderError,
        )

        mock_instance = mock_provider.return_value

        mock_instance.analyze_complaint.side_effect = (
            AIProviderError(
                "Test AI provider failure."
            )
        )

        self.client.force_authenticate(
            user=self.officer
        )

        response = self.client.post(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )

        self.assertIn(
            "Test AI provider failure",
            response.data["detail"],
        )