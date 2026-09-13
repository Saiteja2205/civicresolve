from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from complaints.models import (
    Complaint,
    ComplaintAssignment,
    ComplaintHistory,
    ComplaintSLA,
    SLAPolicy,
)
from organizations.models import Category, Department


class Day28E2ETests(APITestCase):
    """
    HTTP-level end-to-end tests for the CivicResolve API.

    These tests use the actual REST endpoints and mock only the
    external Gemini API call so the test suite remains deterministic.
    """

    def setUp(self):
        self.password = "TestPassword123!"

        self.department = Department.objects.create(
            name="Water Supply",
            description="Water-related complaints.",
            is_active=True,
        )

        self.category = Category.objects.create(
            name="Water Leakage",
            description="Complaints about water leakage.",
            department=self.department,
            is_active=True,
        )

        self.sla_high = SLAPolicy.objects.create(
            priority=Complaint.Priority.HIGH,
            response_time_hours=4,
            resolution_time_hours=24,
            is_active=True,
        )

        self.sla_medium = SLAPolicy.objects.create(
            priority=Complaint.Priority.MEDIUM,
            response_time_hours=8,
            resolution_time_hours=48,
            is_active=True,
        )

        self.citizen = User.objects.create_user(
            email="citizen.day28@example.com",
            password=self.password,
            role=User.Role.USER,
            phone="9876543210",
            first_name="Test",
            last_name="Citizen",
            is_active=True,
        )

        self.officer = User.objects.create_user(
            email="officer.day28@example.com",
            password=self.password,
            role=User.Role.OFFICER,
            phone="9876543211",
            first_name="Test",
            last_name="Officer",
            department=self.department,
            is_active=True,
        )

        self.system_user = User.objects.create_superuser(
            email="system@civicresolve.local",
            password=self.password,
            role=User.Role.ADMIN,
            first_name="CivicResolve",
            last_name="System",
        )

        self.admin = User.objects.create_superuser(
            email="admin.day28@example.com",
            password=self.password,
            role=User.Role.ADMIN,
            first_name="Test",
            last_name="Admin",
        )

    def get_token(self, email):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "email": email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        return (
            response.data["access"],
            response.data["refresh"],
        )

    def authenticate(self, email):
        access, refresh = self.get_token(email)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access}"
        )

        return access, refresh

    def test_01_jwt_login_and_current_user(self):
        """
        Verify JWT login and the current-user endpoint.
        """
        access, refresh = self.authenticate(
            self.citizen.email
        )

        self.assertTrue(access)
        self.assertTrue(refresh)

        response = self.client.get(
            reverse("current-user")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        self.assertEqual(
            response.data["email"],
            self.citizen.email,
        )

        self.assertEqual(
            response.data["role"],
            User.Role.USER,
        )

    def test_02_refresh_token_endpoint(self):
        """
        Verify JWT refresh through the actual API.
        """
        _, refresh = self.get_token(
            self.citizen.email
        )

        response = self.client.post(
            reverse("token_refresh"),
            {
                "refresh": refresh,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        self.assertIn(
            "access",
            response.data,
        )

    @patch(
        "complaints.services.ai_analysis_service.GeminiProvider.analyze_complaint"
    )
    def test_03_citizen_creates_complaint_and_workflow_completes(
        self,
        mock_analyze_complaint,
    ):
        """
        Complete HTTP workflow:

        Citizen
            -> complaint creation
            -> AI analysis
            -> routing
            -> officer assignment
            -> acknowledgement
            -> work started
            -> resolution
            -> admin closure
        """
        mock_analyze_complaint.return_value = """
        {
            "summary": "Water is continuously leaking from a damaged public pipeline.",
            "explanation": "The complaint concerns water leakage and should be handled by the water department.",
            "predicted_category": %d,
            "predicted_department": %d,
            "predicted_priority": "HIGH",
            "urgency_score": 85,
            "confidence_score": 94
        }
        """ % (
            self.category.id,
            self.department.id,
        )

        self.authenticate(
            self.citizen.email
        )

        response = self.client.post(
            reverse("complaint-list"),
            {
                "category": self.category.id,
                "title": "Major water pipeline leakage",
                "description": (
                    "There is continuous water leakage "
                    "from a damaged pipeline near our street."
                ),
                "location": "Main Road",
                "latitude": 17.3850,
                "longitude": 78.4867,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.data,
        )

        complaint_id = response.data["id"]

        complaint = Complaint.objects.get(
            id=complaint_id
        )

        self.assertEqual(
            complaint.user_id,
            self.citizen.id,
        )

        self.assertEqual(
            complaint.category_id,
            self.category.id,
        )

        self.assertEqual(
            complaint.priority,
            Complaint.Priority.HIGH,
        )

        self.assertEqual(
            complaint.status,
            Complaint.Status.ASSIGNED,
        )

        self.assertTrue(
            complaint.ticket_number
        )

        self.assertTrue(
            hasattr(complaint, "analysis")
        )

        analysis = complaint.analysis

        self.assertEqual(
            analysis.predicted_category_id,
            self.category.id,
        )

        self.assertEqual(
            analysis.predicted_department_id,
            self.department.id,
        )

        self.assertEqual(
            analysis.predicted_priority,
            Complaint.Priority.HIGH,
        )

        self.assertEqual(
            analysis.confidence_score,
            Decimal("94.00"),
        )

        assignment = ComplaintAssignment.objects.get(
            complaint=complaint,
            unassigned_at__isnull=True,
        )

        self.assertEqual(
            assignment.officer_id,
            self.officer.id,
        )

        self.assertEqual(
            assignment.department_id,
            self.department.id,
        )

        # Citizen retrieves the complaint.
        response = self.client.get(
            reverse(
                "complaint-detail",
                kwargs={"pk": complaint.id},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        self.assertEqual(
            response.data["id"],
            complaint.id,
        )

        self.assertEqual(
            response.data["ticket_number"],
            complaint.ticket_number,
        )

        self.assertIn(
            "ai_analysis",
            response.data,
        )

        self.assertEqual(
            response.data["ai_analysis"][
                "predicted_category"
            ],
            self.category.id,
        )

        # Officer authenticates.
        self.authenticate(
            self.officer.email
        )

        response = self.client.get(
            reverse(
                "complaint-detail",
                kwargs={"pk": complaint.id},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        # Officer acknowledges.
        response = self.client.post(
            reverse(
                "complaint-acknowledge",
                kwargs={"pk": complaint.id},
            ),
            {
                "comment": (
                    "Complaint acknowledged by officer."
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        self.assertEqual(
            response.data["status"],
            Complaint.Status.ACKNOWLEDGED,
        )

        # Officer starts work.
        response = self.client.post(
            reverse(
                "complaint-start",
                kwargs={"pk": complaint.id},
            ),
            {
                "comment": (
                    "Officer started investigating the issue."
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        self.assertEqual(
            response.data["status"],
            Complaint.Status.IN_PROGRESS,
        )

        # Officer resolves.
        response = self.client.post(
            reverse(
                "complaint-resolve",
                kwargs={"pk": complaint.id},
            ),
            {
                "comment": (
                    "Pipeline leakage repaired "
                    "and water supply restored."
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        self.assertEqual(
            response.data["status"],
            Complaint.Status.RESOLVED,
        )

        complaint.refresh_from_db()

        self.assertEqual(
            complaint.status,
            Complaint.Status.RESOLVED,
        )

        self.assertIsNotNone(
            complaint.resolved_at
        )

        # Admin authenticates.
        self.authenticate(
            self.admin.email
        )

        # Admin closes complaint.
        response = self.client.post(
            reverse(
                "complaint-close",
                kwargs={"pk": complaint.id},
            ),
            {
                "comment": (
                    "Resolution verified and complaint closed."
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        self.assertEqual(
            response.data["status"],
            Complaint.Status.CLOSED,
        )

        complaint.refresh_from_db()

        self.assertEqual(
            complaint.status,
            Complaint.Status.CLOSED,
        )

        self.assertIsNotNone(
            complaint.closed_at
        )

        mock_analyze_complaint.assert_called_once()

    def test_04_citizen_can_view_own_history(self):
        """
        Verify citizen access to complaint history.
        """
        complaint = Complaint.objects.create(
            user=self.citizen,
            category=self.category,
            title="History test complaint",
            description=(
                "This complaint is used to test "
                "the history endpoint."
            ),
            status=Complaint.Status.SUBMITTED,
            priority=Complaint.Priority.MEDIUM,
            location="Test Road",
        )

        ComplaintHistory.objects.create(
            complaint=complaint,
            changed_by=self.citizen,
            old_status="",
            new_status=Complaint.Status.SUBMITTED,
            comment="Complaint submitted.",
        )

        self.authenticate(
            self.citizen.email
        )

        response = self.client.get(
            reverse(
                "complaint-history",
                kwargs={"pk": complaint.id},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        self.assertGreaterEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["new_status"],
            Complaint.Status.SUBMITTED,
        )

    def test_05_citizen_can_view_activity(self):
        """
        Verify citizen access to activity.
        """
        complaint = Complaint.objects.create(
            user=self.citizen,
            category=self.category,
            title="Activity test complaint",
            description=(
                "This complaint is used to test "
                "the activity endpoint."
            ),
            status=Complaint.Status.SUBMITTED,
            priority=Complaint.Priority.LOW,
            location="Activity Road",
        )

        ComplaintHistory.objects.create(
            complaint=complaint,
            changed_by=self.citizen,
            old_status="",
            new_status=Complaint.Status.SUBMITTED,
            comment="Complaint submitted.",
        )

        self.authenticate(
            self.citizen.email
        )

        response = self.client.get(
            reverse("user-activity")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        self.assertGreaterEqual(
            len(response.data),
            1,
        )

    def test_06_admin_can_view_sla_endpoint(self):
        """
        Verify the admin-only SLA endpoint.
        """
        self.authenticate(
            self.admin.email
        )

        response = self.client.get(
            reverse("sla-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

    def test_07_officer_cannot_access_admin_sla_endpoint(self):
        """
        Verify SLA endpoint role protection.
        """
        self.authenticate(
            self.officer.email
        )

        response = self.client.get(
            reverse("sla-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            response.data,
        )

    def test_08_citizen_cannot_manually_assign_complaint(self):
        """
        Verify citizens cannot use manual assignment.
        """
        complaint = Complaint.objects.create(
            user=self.citizen,
            category=self.category,
            title="Assignment permission test",
            description=(
                "This complaint tests assignment permissions."
            ),
            status=Complaint.Status.SUBMITTED,
            priority=Complaint.Priority.MEDIUM,
            location="Permission Road",
        )

        self.authenticate(
            self.citizen.email
        )

        response = self.client.post(
            reverse(
                "complaint-assign",
                kwargs={"pk": complaint.id},
            ),
            {
                "officer_id": self.officer.id,
                "department_id": self.department.id,
                "reason": "Unauthorized assignment attempt.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            response.data,
        )

    def test_09_citizen_cannot_acknowledge_complaint(self):
        """
        Verify citizens cannot perform officer actions.
        """
        complaint = Complaint.objects.create(
            user=self.citizen,
            category=self.category,
            title="Officer permission test",
            description=(
                "This complaint tests officer-only actions."
            ),
            status=Complaint.Status.ASSIGNED,
            priority=Complaint.Priority.MEDIUM,
            location="Officer Road",
        )

        self.authenticate(
            self.citizen.email
        )

        response = self.client.post(
            reverse(
                "complaint-acknowledge",
                kwargs={"pk": complaint.id},
            ),
            {
                "comment": "Unauthorized acknowledgement.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            response.data,
        )

    def test_10_unauthenticated_user_cannot_access_complaints(self):
        """
        Verify authentication is required.
        """
        self.client.credentials()

        response = self.client.get(
            reverse("complaint-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            response.data,
        )

    def test_11_active_category_endpoint_requires_authentication(self):
        """
        Verify organization endpoints require authentication.
        """
        self.client.credentials()

        response = self.client.get(
            reverse("active-category-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            response.data,
        )

    def test_12_authenticated_user_can_list_active_categories(self):
        """
        Verify authenticated users can list active categories.
        """
        self.authenticate(
            self.citizen.email
        )

        response = self.client.get(
            reverse("active-category-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        category_ids = {
            item["id"]
            for item in response.data
        }

        self.assertIn(
            self.category.id,
            category_ids,
        )

    def test_13_admin_can_list_active_officers(self):
        """
        Verify admin access to active officers.
        """
        self.authenticate(
            self.admin.email
        )

        response = self.client.get(
            reverse("active-officer-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        officer_ids = {
            item["id"]
            for item in response.data
        }

        self.assertIn(
            self.officer.id,
            officer_ids,
        )

    def test_14_officer_list_endpoint_is_admin_only(self):
        """
        Verify officer enumeration is admin-only.
        """
        self.authenticate(
            self.officer.email
        )

        response = self.client.get(
            reverse("active-officer-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            response.data,
        )

    def test_15_profile_endpoint_returns_authenticated_user(self):
        """
        Verify authenticated profile endpoint.
        """
        self.authenticate(
            self.citizen.email
        )

        response = self.client.get(
            reverse("user-profile")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        self.assertEqual(
            response.data["email"],
            self.citizen.email,
        )

        self.assertEqual(
            response.data["role"],
            User.Role.USER,
        )

    def test_16_invalid_complaint_data_is_rejected(self):
        """
        Verify complaint serializer validation.
        """
        self.authenticate(
            self.citizen.email
        )

        response = self.client.post(
            reverse("complaint-list"),
            {
                "category": self.category.id,
                "title": "Bad",
                "description": "Short",
                "location": "X",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.data,
        )

        self.assertNotIn(
            "id",
            response.data,
        )

    def test_17_assignment_endpoint_rejects_missing_officer(self):
        """
        Verify assignment requires an officer.
        """
        complaint = Complaint.objects.create(
            user=self.citizen,
            category=self.category,
            title="Missing officer test",
            description=(
                "This complaint tests missing officer validation."
            ),
            status=Complaint.Status.SUBMITTED,
            priority=Complaint.Priority.MEDIUM,
            location="Assignment Road",
        )

        self.authenticate(
            self.admin.email
        )

        response = self.client.post(
            reverse(
                "complaint-assign",
                kwargs={"pk": complaint.id},
            ),
            {
                "department_id": self.department.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.data,
        )

        self.assertIn(
            "detail",
            response.data,
        )

    def test_18_assignment_endpoint_rejects_wrong_department(self):
        """
        Verify officer and department must match.
        """
        other_department = Department.objects.create(
            name="Roads Department",
            description="Road-related complaints.",
            is_active=True,
        )

        complaint = Complaint.objects.create(
            user=self.citizen,
            category=self.category,
            title="Wrong department test",
            description=(
                "This complaint tests department validation."
            ),
            status=Complaint.Status.SUBMITTED,
            priority=Complaint.Priority.MEDIUM,
            location="Department Road",
        )

        self.authenticate(
            self.admin.email
        )

        response = self.client.post(
            reverse(
                "complaint-assign",
                kwargs={"pk": complaint.id},
            ),
            {
                "officer_id": self.officer.id,
                "department_id": other_department.id,
                "reason": "Wrong department test.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.data,
        )

        self.assertIn(
            "detail",
            response.data,
        )

    def test_19_citizen_cannot_view_another_citizens_complaint(self):
        """
        Verify citizen queryset isolation.
        """
        other_citizen = User.objects.create_user(
            email="other.day28@example.com",
            password=self.password,
            role=User.Role.USER,
            phone="9876543212",
            is_active=True,
        )

        complaint = Complaint.objects.create(
            user=other_citizen,
            category=self.category,
            title="Private complaint",
            description=(
                "This complaint belongs to another citizen."
            ),
            status=Complaint.Status.SUBMITTED,
            priority=Complaint.Priority.MEDIUM,
            location="Private Road",
        )

        self.authenticate(
            self.citizen.email
        )

        response = self.client.get(
            reverse(
                "complaint-detail",
                kwargs={"pk": complaint.id},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            response.data,
        )

    def test_20_officer_cannot_view_unassigned_complaint(self):
        """
        Verify officer queryset isolation.
        """
        complaint = Complaint.objects.create(
            user=self.citizen,
            category=self.category,
            title="Unassigned officer test",
            description=(
                "This complaint should not be visible "
                "to the officer without assignment."
            ),
            status=Complaint.Status.SUBMITTED,
            priority=Complaint.Priority.MEDIUM,
            location="Officer Visibility Road",
        )

        self.authenticate(
            self.officer.email
        )

        response = self.client.get(
            reverse(
                "complaint-detail",
                kwargs={"pk": complaint.id},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            response.data,
        )

    def test_21_assignment_list_is_role_scoped(self):
        """
        Verify citizens cannot see assignment records.
        """
        complaint = Complaint.objects.create(
            user=self.citizen,
            category=self.category,
            title="Assignment visibility test",
            description=(
                "This complaint tests assignment list visibility."
            ),
            status=Complaint.Status.ASSIGNED,
            priority=Complaint.Priority.MEDIUM,
            location="Visibility Road",
        )

        ComplaintAssignment.objects.create(
            complaint=complaint,
            department=self.department,
            officer=self.officer,
            assigned_by=self.admin,
            reason="Test assignment.",
        )

        self.authenticate(
            self.citizen.email
        )

        response = self.client.get(
            reverse("assignment-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        self.assertEqual(
            response.data,
            [],
        )

    @patch(
        "complaints.services.ai_analysis_service.GeminiProvider.analyze_complaint"
    )
    def test_22_ai_failure_returns_complaint_to_submitted(
        self,
        mock_analyze_complaint,
    ):
        """
        Verify graceful AI failure through HTTP complaint creation.
        """
        from complaints.services.ai_provider import AIProviderError

        mock_analyze_complaint.side_effect = AIProviderError(
            "Simulated AI provider failure."
        )

        self.authenticate(
            self.citizen.email
        )

        response = self.client.post(
            reverse("complaint-list"),
            {
                "category": self.category.id,
                "title": "AI failure test complaint",
                "description": (
                    "This complaint tests the system "
                    "when the AI provider fails."
                ),
                "location": "AI Failure Road",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.data,
        )

        complaint = Complaint.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(
            complaint.status,
            Complaint.Status.SUBMITTED,
        )

        self.assertFalse(
            ComplaintAssignment.objects.filter(
                complaint=complaint
            ).exists()
        )

        mock_analyze_complaint.assert_called_once()

    @patch(
        "complaints.services.ai_analysis_service.GeminiProvider.analyze_complaint"
    )
    def test_23_full_workflow_creates_expected_history(
        self,
        mock_analyze_complaint,
    ):
        """
        Verify the HTTP workflow creates the expected audit trail.
        """
        mock_analyze_complaint.return_value = """
        {
            "summary": "Water leakage requires attention.",
            "explanation": "The issue matches the water leakage category.",
            "predicted_category": %d,
            "predicted_department": %d,
            "predicted_priority": "MEDIUM",
            "urgency_score": 70,
            "confidence_score": 90
        }
        """ % (
            self.category.id,
            self.department.id,
        )

        self.authenticate(
            self.citizen.email
        )

        response = self.client.post(
            reverse("complaint-list"),
            {
                "category": self.category.id,
                "title": "History workflow test",
                "description": (
                    "Water is leaking continuously "
                    "from a damaged public pipeline."
                ),
                "location": "Audit Road",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.data,
        )

        complaint = Complaint.objects.get(
            id=response.data["id"]
        )

        self.authenticate(
            self.officer.email
        )

        response = self.client.post(
            reverse(
                "complaint-acknowledge",
                kwargs={"pk": complaint.id},
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        response = self.client.post(
            reverse(
                "complaint-start",
                kwargs={"pk": complaint.id},
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        response = self.client.post(
            reverse(
                "complaint-resolve",
                kwargs={"pk": complaint.id},
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        self.authenticate(
            self.admin.email
        )

        response = self.client.post(
            reverse(
                "complaint-close",
                kwargs={"pk": complaint.id},
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data,
        )

        history = ComplaintHistory.objects.filter(
            complaint=complaint
        ).order_by("created_at")

        statuses = list(
            history.values_list(
                "new_status",
                flat=True,
            )
        )

        self.assertIn(
            Complaint.Status.SUBMITTED,
            statuses,
        )

        self.assertIn(
            Complaint.Status.ASSIGNED,
            statuses,
        )

        self.assertIn(
            Complaint.Status.ACKNOWLEDGED,
            statuses,
        )

        self.assertIn(
            Complaint.Status.IN_PROGRESS,
            statuses,
        )

        self.assertIn(
            Complaint.Status.RESOLVED,
            statuses,
        )

        self.assertIn(
            Complaint.Status.CLOSED,
            statuses,
        )

        mock_analyze_complaint.assert_called_once()