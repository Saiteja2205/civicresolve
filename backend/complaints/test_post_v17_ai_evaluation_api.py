from unittest.mock import patch

from django.urls import reverse

from rest_framework.test import APITestCase

from accounts.models import User


class AIEvaluationAPITests(
    APITestCase
):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="evaluation.admin@test.local",
            password="TestPassword123!",
            role=User.Role.ADMIN,
            is_active=True,
        )

        self.officer = User.objects.create_user(
            email="evaluation.officer@test.local",
            password="TestPassword123!",
            role=User.Role.OFFICER,
            is_active=True,
        )

        self.citizen = User.objects.create_user(
            email="evaluation.citizen@test.local",
            password="TestPassword123!",
            role=User.Role.USER,
            is_active=True,
        )

        self.url = reverse(
            "ai-evaluation"
        )

        self.mock_report = {
            "total_cases": 6,
            "category_accuracy_percent": 100.0,
            "priority_accuracy_percent": 100.0,
            "urgency_mae": 6.67,
            "overall_pass_rate_percent": 100.0,
            "passed_cases": 6,
            "failed_cases": 0,
            "results": [],
        }

    @patch(
        "complaints.ai_evaluation_views.run_evaluation"
    )
    def test_admin_can_run_evaluation(
        self,
        mock_run_evaluation,
    ):
        mock_run_evaluation.return_value = (
            self.mock_report
        )

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            self.url
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["total_cases"],
            6,
        )

        self.assertEqual(
            response.data[
                "category_accuracy_percent"
            ],
            100.0,
        )

        mock_run_evaluation.assert_called_once()

    @patch(
        "complaints.ai_evaluation_views.run_evaluation"
    )
    def test_officer_cannot_run_evaluation(
        self,
        mock_run_evaluation,
    ):
        self.client.force_authenticate(
            user=self.officer
        )

        response = self.client.post(
            self.url
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        mock_run_evaluation.assert_not_called()

    @patch(
        "complaints.ai_evaluation_views.run_evaluation"
    )
    def test_citizen_cannot_run_evaluation(
        self,
        mock_run_evaluation,
    ):
        self.client.force_authenticate(
            user=self.citizen
        )

        response = self.client.post(
            self.url
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        mock_run_evaluation.assert_not_called()