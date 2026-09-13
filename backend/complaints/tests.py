from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from complaints.models import (
    Complaint,
    ComplaintAnalysis,
    ComplaintAssignment,
    ComplaintHistory,
    ComplaintSLA,
    SLAPolicy,
)
from complaints.services.assignment_service import (
    ComplaintAssignmentError,
    assign_complaint,
)
from complaints.services.complaint_service import (
    change_complaint_status,
)
from complaints.services.sla_monitoring_service import (
    check_complaint_sla,
)
from complaints.services.sla_service import (
    create_complaint_sla,
)
from organizations.models import Category, Department


User = get_user_model()


class ComplaintStatusServiceTests(TestCase):

    def setUp(self):
        self.department = Department.objects.create(
            name="IT Support"
        )

        self.category = Category.objects.create(
            name="Wi-Fi",
            department=self.department,
        )

        self.user = User.objects.create_user(
            email="user@test.com",
            password="testpassword",
            role="USER",
        )

        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="testpassword",
            role="ADMIN",
        )

        self.complaint = Complaint.objects.create(
            user=self.user,
            category=self.category,
            title="Wi-Fi issue",
            description="Wi-Fi is not working.",
        )

    def test_valid_status_transition_creates_history(self):
        change_complaint_status(
            complaint=self.complaint,
            new_status=Complaint.Status.ASSIGNED,
            changed_by=self.admin,
            comment="Assigned for testing.",
        )

        self.complaint.refresh_from_db()

        self.assertEqual(
            self.complaint.status,
            Complaint.Status.ASSIGNED,
        )

        self.assertEqual(
            self.complaint.history.count(),
            1,
        )

        history = self.complaint.history.first()

        self.assertEqual(
            history.old_status,
            Complaint.Status.SUBMITTED,
        )

        self.assertEqual(
            history.new_status,
            Complaint.Status.ASSIGNED,
        )

        self.assertEqual(
            history.changed_by,
            self.admin,
        )

    def test_invalid_transition_is_rejected(self):
        with self.assertRaises(ValueError):
            change_complaint_status(
                complaint=self.complaint,
                new_status=Complaint.Status.CLOSED,
                changed_by=self.admin,
            )

        self.complaint.refresh_from_db()

        self.assertEqual(
            self.complaint.status,
            Complaint.Status.SUBMITTED,
        )

        self.assertEqual(
            self.complaint.history.count(),
            0,
        )


class ComplaintAssignmentIntegrationTests(TestCase):

    def setUp(self):
        self.department = Department.objects.create(
            name="IT Support"
        )

        self.category = Category.objects.create(
            name="Network",
            department=self.department,
        )

        self.user = User.objects.create_user(
            email="user@test.com",
            password="testpassword",
            role=User.Role.USER,
        )

        self.officer1 = User.objects.create_user(
            email="officer1@test.com",
            password="testpassword",
            role=User.Role.OFFICER,
            department=self.department,
        )

        self.officer2 = User.objects.create_user(
            email="officer2@test.com",
            password="testpassword",
            role=User.Role.OFFICER,
            department=self.department,
        )

        self.system_user = User.objects.create_user(
            email="system@civicresolve.local",
            password="testpassword",
            role=User.Role.ADMIN,
        )

        self.complaint = Complaint.objects.create(
            user=self.user,
            category=self.category,
            title="Network outage",
            description="Campus network is unavailable.",
            status=Complaint.Status.AI_ANALYZING,
            priority=Complaint.Priority.MEDIUM,
        )

        ComplaintAnalysis.objects.create(
            complaint=self.complaint,
            summary="Campus network is unavailable.",
            predicted_category=self.category,
            predicted_department=self.department,
            predicted_priority=Complaint.Priority.MEDIUM,
            urgency_score=70,
            confidence_score=95,
            model_name="Test-AI",
        )

    @patch(
        "complaints.services.assignment_service.get_system_assignment_user"
    )
    def test_assign_complaint_selects_least_loaded_officer(
        self,
        mock_get_system_user,
    ):
        mock_get_system_user.return_value = self.system_user

        existing_complaint = Complaint.objects.create(
            user=self.user,
            category=self.category,
            title="Existing complaint",
            description="Existing network complaint.",
            status=Complaint.Status.ASSIGNED,
        )

        ComplaintAssignment.objects.create(
            complaint=existing_complaint,
            department=self.department,
            officer=self.officer1,
            assigned_by=self.system_user,
            reason="Existing assignment for workload test.",
        )

        assignment = assign_complaint(self.complaint)

        self.assertEqual(
            assignment.officer,
            self.officer2,
        )

        self.assertEqual(
            assignment.department,
            self.department,
        )

        self.assertEqual(
            assignment.assigned_by,
            self.system_user,
        )

        self.complaint.refresh_from_db()

        self.assertEqual(
            self.complaint.status,
            Complaint.Status.ASSIGNED,
        )

        self.assertEqual(
            self.complaint.history.count(),
            1,
        )

        history = self.complaint.history.first()

        self.assertEqual(
            history.old_status,
            Complaint.Status.AI_ANALYZING,
        )

        self.assertEqual(
            history.new_status,
            Complaint.Status.ASSIGNED,
        )

    @patch(
        "complaints.services.assignment_service.get_system_assignment_user"
    )
    def test_duplicate_assignment_is_rejected(
        self,
        mock_get_system_user,
    ):
        mock_get_system_user.return_value = self.system_user

        assignment = ComplaintAssignment.objects.create(
            complaint=self.complaint,
            department=self.department,
            officer=self.officer1,
            assigned_by=self.system_user,
            reason="Existing assignment.",
        )

        self.assertIsNotNone(assignment)

        with self.assertRaises(
            ComplaintAssignmentError
        ):
            assign_complaint(self.complaint)


class ComplaintSLATests(TestCase):

    def setUp(self):
        self.department = Department.objects.create(
            name="IT Support"
        )

        self.category = Category.objects.create(
            name="Network",
            department=self.department,
        )

        self.user = User.objects.create_user(
            email="user@test.com",
            password="testpassword",
            role=User.Role.USER,
        )

        self.policy = SLAPolicy.objects.create(
            priority=Complaint.Priority.MEDIUM,
            response_time_hours=48,
            resolution_time_hours=96,
        )

        self.complaint = Complaint.objects.create(
            user=self.user,
            category=self.category,
            title="SLA test",
            description="Testing SLA calculation.",
            priority=Complaint.Priority.MEDIUM,
        )

    def test_sla_deadlines_are_calculated_from_creation_time(self):
        sla = create_complaint_sla(
            self.complaint
        )

        expected_response = (
            self.complaint.created_at
            + timedelta(hours=48)
        )

        expected_resolution = (
            self.complaint.created_at
            + timedelta(hours=96)
        )

        self.assertEqual(
            sla.response_deadline,
            expected_response,
        )

        self.assertEqual(
            sla.resolution_deadline,
            expected_resolution,
        )

        self.assertEqual(
            sla.policy,
            self.policy,
        )

    def test_sla_creation_is_idempotent(self):
        first_sla = create_complaint_sla(
            self.complaint
        )

        second_sla = create_complaint_sla(
            self.complaint
        )

        self.assertEqual(
            first_sla.id,
            second_sla.id,
        )

        self.assertEqual(
            ComplaintSLA.objects.filter(
                complaint=self.complaint
            ).count(),
            1,
        )


class ComplaintSLAMonitoringTests(TestCase):

    def setUp(self):
        self.department = Department.objects.create(
            name="IT Support"
        )

        self.category = Category.objects.create(
            name="Network",
            department=self.department,
        )

        self.user = User.objects.create_user(
            email="user@test.com",
            password="testpassword",
            role=User.Role.USER,
        )

        self.complaint = Complaint.objects.create(
            user=self.user,
            category=self.category,
            title="SLA monitoring test",
            description="Testing SLA monitoring.",
            status=Complaint.Status.IN_PROGRESS,
            priority=Complaint.Priority.MEDIUM,
        )

        self.policy = SLAPolicy.objects.create(
            priority=Complaint.Priority.MEDIUM,
            response_time_hours=48,
            resolution_time_hours=96,
        )

        self.sla = ComplaintSLA.objects.create(
            complaint=self.complaint,
            policy=self.policy,
            response_deadline=(
                timezone.now() + timedelta(hours=2)
            ),
            resolution_deadline=(
                timezone.now() + timedelta(hours=4)
            ),
        )

    def test_no_breach_when_deadlines_are_in_future(self):
        result = check_complaint_sla(
            self.complaint
        )

        self.assertFalse(
            result["response_breached"]
        )

        self.assertFalse(
            result["resolution_breached"]
        )

        self.assertFalse(
            result["escalated"]
        )

        self.complaint.refresh_from_db()

        self.assertEqual(
            self.complaint.status,
            Complaint.Status.IN_PROGRESS,
        )

    def test_resolution_breach_escalates_complaint(self):
        self.sla.resolution_deadline = (
            timezone.now()
            - timedelta(hours=1)
        )

        self.sla.save()

        result = check_complaint_sla(
            self.complaint
        )

        self.assertTrue(
            result["resolution_breached"]
        )

        self.assertTrue(
            result["escalated"]
        )

        self.complaint.refresh_from_db()

        self.assertEqual(
            self.complaint.status,
            Complaint.Status.ESCALATED,
        )

        self.assertEqual(
            self.complaint.history.count(),
            1,
        )

        history = self.complaint.history.first()

        self.assertEqual(
            history.old_status,
            Complaint.Status.IN_PROGRESS,
        )

        self.assertEqual(
            history.new_status,
            Complaint.Status.ESCALATED,
        )

        self.assertIsNone(
            history.changed_by
        )

    def test_repeated_monitoring_does_not_duplicate_escalation(
        self,
    ):
        self.sla.resolution_deadline = (
            timezone.now()
            - timedelta(hours=1)
        )

        self.sla.save()

        first_result = check_complaint_sla(
            self.complaint
        )

        second_result = check_complaint_sla(
            self.complaint
        )

        self.assertTrue(
            first_result["escalated"]
        )

        self.assertFalse(
            second_result["escalated"]
        )

        self.assertEqual(
            self.complaint.history.filter(
                new_status=Complaint.Status.ESCALATED
            ).count(),
            1,
        )


class ComplaintAPITestBase(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.department = Department.objects.create(
            name="Public Works"
        )

        self.category = Category.objects.create(
            name="Road Repair",
            department=self.department,
        )

        self.user = User.objects.create_user(
            email="citizen@test.com",
            password="testpassword",
            role=User.Role.USER,
        )

        self.other_user = User.objects.create_user(
            email="other@test.com",
            password="testpassword",
            role=User.Role.USER,
        )

        self.officer = User.objects.create_user(
            email="officer@test.com",
            password="testpassword",
            role=User.Role.OFFICER,
            department=self.department,
        )

        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="testpassword",
            role=User.Role.ADMIN,
        )

        self.complaint = Complaint.objects.create(
            user=self.user,
            category=self.category,
            title="Road repair needed",
            description="There is a damaged road near the main gate.",
            status=Complaint.Status.ASSIGNED,
            priority=Complaint.Priority.MEDIUM,
        )

        ComplaintAssignment.objects.create(
            complaint=self.complaint,
            department=self.department,
            officer=self.officer,
            assigned_by=self.admin,
            reason="Test assignment.",
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)


class ComplaintAPIAccessTests(ComplaintAPITestBase):

    def test_unauthenticated_complaint_list_is_rejected(self):
        response = self.client.get(
            reverse("complaint-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_citizen_can_list_own_complaints(self):
        self.authenticate(self.user)

        response = self.client.get(
            reverse("complaint-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = [
            item["id"]
            for item in response.data
        ]

        self.assertIn(
            self.complaint.id,
            returned_ids,
        )

    def test_citizen_cannot_see_another_citizens_complaint(self):
        self.authenticate(self.other_user)

        response = self.client.get(
            reverse(
                "complaint-detail",
                args=[self.complaint.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_officer_can_access_assigned_complaint(self):
        self.authenticate(self.officer)

        response = self.client.get(
            reverse(
                "complaint-detail",
                args=[self.complaint.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_admin_can_access_complaint(self):
        self.authenticate(self.admin)

        response = self.client.get(
            reverse(
                "complaint-detail",
                args=[self.complaint.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )


class ComplaintAPIPermissionTests(ComplaintAPITestBase):

    def test_citizen_cannot_update_complaint(self):
        self.authenticate(self.user)

        response = self.client.patch(
            reverse(
                "complaint-detail",
                args=[self.complaint.id],
            ),
            {
                "title": "Citizen attempted update",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_citizen_cannot_assign_complaint(self):
        self.authenticate(self.user)

        response = self.client.post(
            reverse(
                "complaint-assign",
                args=[self.complaint.id],
            ),
            {
                "officer_id": self.officer.id,
                "department_id": self.department.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_officer_cannot_close_complaint(self):
        self.authenticate(self.officer)

        response = self.client.post(
            reverse(
                "complaint-close",
                args=[self.complaint.id],
            ),
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_officer_cannot_assign_complaint(self):
        self.authenticate(self.officer)

        response = self.client.post(
            reverse(
                "complaint-assign",
                args=[self.complaint.id],
            ),
            {
                "officer_id": self.officer.id,
                "department_id": self.department.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_can_access_sla_endpoint(self):
        self.authenticate(self.admin)

        response = self.client.get(
            reverse("sla-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_citizen_cannot_access_sla_endpoint(self):
        self.authenticate(self.user)

        response = self.client.get(
            reverse("sla-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


class ComplaintHistoryAPITests(ComplaintAPITestBase):

    def test_authenticated_user_can_access_history_endpoint(self):
        ComplaintHistory.objects.create(
            complaint=self.complaint,
            changed_by=self.admin,
            old_status=Complaint.Status.SUBMITTED,
            new_status=Complaint.Status.ASSIGNED,
            comment="Test history entry.",
        )

        self.authenticate(self.user)

        response = self.client.get(
            reverse(
                "complaint-history",
                args=[self.complaint.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

    def test_other_citizen_cannot_access_history(self):
        self.authenticate(self.other_user)

        response = self.client.get(
            reverse(
                "complaint-history",
                args=[self.complaint.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class ComplaintReopenAPITests(ComplaintAPITestBase):

    def test_citizen_can_reopen_own_resolved_complaint(self):
        self.complaint.status = Complaint.Status.RESOLVED
        self.complaint.save(
            update_fields=["status"]
        )

        self.authenticate(self.user)

        response = self.client.post(
            reverse(
                "complaint-reopen",
                args=[self.complaint.id],
            ),
            {
                "comment": (
                    "The issue is still present "
                    "after the previous resolution."
                )
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.complaint.refresh_from_db()

        self.assertEqual(
            self.complaint.status,
            Complaint.Status.REOPENED,
        )

        self.assertEqual(
            self.complaint.history.count(),
            1,
        )

    def test_reopen_requires_reason(self):
        self.complaint.status = Complaint.Status.RESOLVED
        self.complaint.save(
            update_fields=["status"]
        )

        self.authenticate(self.user)

        response = self.client.post(
            reverse(
                "complaint-reopen",
                args=[self.complaint.id],
            ),
            {
                "comment": "Too short",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_citizen_cannot_reopen_another_users_complaint(self):
        self.complaint.status = Complaint.Status.RESOLVED
        self.complaint.save(
            update_fields=["status"]
        )

        self.authenticate(self.other_user)

        response = self.client.post(
            reverse(
                "complaint-reopen",
                args=[self.complaint.id],
            ),
            {
                "comment": (
                    "Trying to reopen another citizen's complaint."
                )
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_admin_cannot_use_citizen_reopen_endpoint(self):
        self.complaint.status = Complaint.Status.RESOLVED
        self.complaint.save(
            update_fields=["status"]
        )

        self.authenticate(self.admin)

        response = self.client.post(
            reverse(
                "complaint-reopen",
                args=[self.complaint.id],
            ),
            {
                "comment": (
                    "Admin attempting citizen reopen."
                )
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


class ComplaintValidationAPITests(ComplaintAPITestBase):

    @patch("complaints.views.create_complaint")
    def test_complaint_creation_accepts_valid_data(
        self,
        mock_create_complaint,
    ):
        new_complaint = Complaint(
            id=999,
            user=self.user,
            category=self.category,
            title="Street light problem",
            description="The street light is not working.",
        )

        mock_create_complaint.return_value = new_complaint

        self.authenticate(self.user)

        response = self.client.post(
            reverse("complaint-list"),
            {
                "category": self.category.id,
                "title": "Street light problem",
                "description": (
                    "The street light is not working."
                ),
                "location": "Main road",
                "latitude": 17.385,
                "longitude": 78.4867,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

    def test_complaint_creation_rejects_short_title(self):
        self.authenticate(self.user)

        response = self.client.post(
            reverse("complaint-list"),
            {
                "category": self.category.id,
                "title": "Bad",
                "description": (
                    "This description is long enough."
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_complaint_creation_rejects_short_description(self):
        self.authenticate(self.user)

        response = self.client.post(
            reverse("complaint-list"),
            {
                "category": self.category.id,
                "title": "Valid complaint title",
                "description": "Short",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_complaint_creation_rejects_invalid_latitude(self):
        self.authenticate(self.user)

        response = self.client.post(
            reverse("complaint-list"),
            {
                "category": self.category.id,
                "title": "Invalid location complaint",
                "description": (
                    "This complaint has an invalid latitude."
                ),
                "latitude": 100,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_complaint_creation_rejects_invalid_longitude(self):
        self.authenticate(self.user)

        response = self.client.post(
            reverse("complaint-list"),
            {
                "category": self.category.id,
                "title": "Invalid location complaint",
                "description": (
                    "This complaint has an invalid longitude."
                ),
                "longitude": 200,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )