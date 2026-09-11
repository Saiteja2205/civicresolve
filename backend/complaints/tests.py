from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

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