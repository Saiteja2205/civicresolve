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
from complaints.services.sla_monitoring_service import (
    SLAMonitoringError,
    check_complaint_sla,
)
from complaints.services.sla_service import (
    SLAError,
    create_complaint_sla,
)
from organizations.models import Category, Department


User = get_user_model()


class Day26TestBase(TestCase):
    """
    Shared setup for Day 26 automatic assignment and SLA tests.
    """

    def setUp(self):
        self.department = Department.objects.create(
            name="IT Support",
            is_active=True,
        )

        self.category = Category.objects.create(
            name="Network Issues",
            department=self.department,
            is_active=True,
        )

        self.citizen = User.objects.create_user(
            email="citizen.day26@example.com",
            password="TestPass123!",
            role=User.Role.USER,
        )

        self.admin = User.objects.create_user(
            email="admin.day26@example.com",
            password="TestPass123!",
            role=User.Role.ADMIN,
            is_active=True,
        )

        self.system_user = User.objects.create_user(
            email="system@civicresolve.local",
            password="SystemPass123!",
            role=User.Role.ADMIN,
            is_active=True,
        )

    def create_officer(
        self,
        email="officer.day26@example.com",
        *,
        is_active=True,
        department=None,
    ):
        return User.objects.create_user(
            email=email,
            password="TestPass123!",
            role=User.Role.OFFICER,
            department=department or self.department,
            is_active=is_active,
        )

    def create_complaint(
        self,
        *,
        title="Internet connection issue",
        status=Complaint.Status.AI_ANALYZING,
        priority=Complaint.Priority.MEDIUM,
    ):
        return Complaint.objects.create(
            user=self.citizen,
            category=self.category,
            title=title,
            description="Internet service is not working.",
            status=status,
            priority=priority,
        )

    def create_analysis(
        self,
        complaint,
        *,
        category=None,
        department=None,
        priority=None,
    ):
        return ComplaintAnalysis.objects.create(
            complaint=complaint,
            summary="Internet connectivity complaint.",
            explanation=(
                "The complaint concerns a network "
                "connectivity problem."
            ),
            predicted_category=category or self.category,
            predicted_department=department or self.department,
            predicted_priority=priority or complaint.priority,
            urgency_score="70.00",
            confidence_score="95.00",
            model_name="test-model",
        )


class AutomaticAssignmentTests(Day26TestBase):
    """
    Verify that automatic assignment remains safe and transactional.
    """

    def test_assignment_creates_assignment_record(self):
        complaint = self.create_complaint()
        self.create_analysis(complaint)
        self.create_officer()

        assignment = assign_complaint(complaint)

        self.assertEqual(
            ComplaintAssignment.objects.filter(
                complaint=complaint,
                unassigned_at__isnull=True,
            ).count(),
            1,
        )

        self.assertEqual(assignment.complaint, complaint)
        self.assertEqual(assignment.department, self.department)
        self.assertEqual(assignment.assigned_by, self.system_user)

    def test_assignment_changes_status_to_assigned(self):
        complaint = self.create_complaint()
        self.create_analysis(complaint)
        self.create_officer()

        assign_complaint(complaint)

        complaint.refresh_from_db()

        self.assertEqual(
            complaint.status,
            Complaint.Status.ASSIGNED,
        )

    def test_assignment_creates_history_record(self):
        complaint = self.create_complaint()
        self.create_analysis(complaint)
        self.create_officer()

        assign_complaint(complaint)

        history = ComplaintHistory.objects.filter(
            complaint=complaint,
            new_status=Complaint.Status.ASSIGNED,
        ).first()

        self.assertIsNotNone(history)
        self.assertEqual(
            history.old_status,
            Complaint.Status.AI_ANALYZING,
        )
        self.assertEqual(
            history.changed_by,
            self.system_user,
        )

    def test_assignment_uses_system_assignment_user(self):
        complaint = self.create_complaint()
        self.create_analysis(complaint)
        self.create_officer()

        assignment = assign_complaint(complaint)

        self.assertEqual(
            assignment.assigned_by.email,
            "system@civicresolve.local",
        )

    def test_assignment_rejects_non_ai_analyzing_complaint(self):
        complaint = self.create_complaint(
            status=Complaint.Status.SUBMITTED,
        )
        self.create_analysis(complaint)

        with self.assertRaises(ComplaintAssignmentError):
            assign_complaint(complaint)

        self.assertFalse(
            ComplaintAssignment.objects.filter(
                complaint=complaint,
            ).exists()
        )

    def test_assignment_rejects_existing_active_assignment(self):
        complaint = self.create_complaint()
        self.create_analysis(complaint)

        officer = self.create_officer(
            email="existing.officer.day26@example.com",
        )

        ComplaintAssignment.objects.create(
            complaint=complaint,
            department=self.department,
            officer=officer,
            assigned_by=self.system_user,
            reason="Existing assignment.",
        )

        with self.assertRaises(ComplaintAssignmentError):
            assign_complaint(complaint)

        self.assertEqual(
            ComplaintAssignment.objects.filter(
                complaint=complaint,
                unassigned_at__isnull=True,
            ).count(),
            1,
        )

    def test_assignment_rolls_back_when_status_change_fails(self):
        complaint = self.create_complaint()
        self.create_analysis(complaint)
        self.create_officer(
            email="rollback.officer.day26@example.com",
        )

        with patch(
            "complaints.services.assignment_service.change_complaint_status",
            side_effect=RuntimeError("Simulated status failure"),
        ):
            with self.assertRaises(RuntimeError):
                assign_complaint(complaint)

        self.assertFalse(
            ComplaintAssignment.objects.filter(
                complaint=complaint,
            ).exists()
        )

        complaint.refresh_from_db()

        self.assertEqual(
            complaint.status,
            Complaint.Status.AI_ANALYZING,
        )


class SLAPolicyTests(Day26TestBase):
    """
    Verify priority-specific SLA policy behavior.
    """

    def create_policy(
        self,
        priority,
        response_hours,
        resolution_hours,
    ):
        return SLAPolicy.objects.create(
            priority=priority,
            response_time_hours=response_hours,
            resolution_time_hours=resolution_hours,
            is_active=True,
        )

    def test_medium_priority_uses_medium_policy(self):
        policy = self.create_policy(
            Complaint.Priority.MEDIUM,
            response_hours=4,
            resolution_hours=24,
        )

        complaint = self.create_complaint(
            priority=Complaint.Priority.MEDIUM,
        )

        before = complaint.created_at

        sla = create_complaint_sla(complaint)

        self.assertEqual(sla.policy, policy)
        self.assertEqual(
            sla.response_deadline,
            before + timedelta(hours=4),
        )
        self.assertEqual(
            sla.resolution_deadline,
            before + timedelta(hours=24),
        )

    def test_high_priority_gets_shorter_deadline(self):
        medium_policy = self.create_policy(
            Complaint.Priority.MEDIUM,
            response_hours=8,
            resolution_hours=48,
        )

        high_policy = self.create_policy(
            Complaint.Priority.HIGH,
            response_hours=2,
            resolution_hours=12,
        )

        medium_complaint = self.create_complaint(
            title="Medium complaint",
            priority=Complaint.Priority.MEDIUM,
        )

        high_complaint = self.create_complaint(
            title="High complaint",
            priority=Complaint.Priority.HIGH,
        )

        medium_sla = create_complaint_sla(medium_complaint)
        high_sla = create_complaint_sla(high_complaint)

        self.assertEqual(medium_sla.policy, medium_policy)
        self.assertEqual(high_sla.policy, high_policy)

        self.assertLess(
            high_sla.policy.response_time_hours,
            medium_sla.policy.response_time_hours,
        )

        self.assertLess(
            high_sla.policy.resolution_time_hours,
            medium_sla.policy.resolution_time_hours,
        )

    def test_critical_priority_uses_critical_policy(self):
        policy = self.create_policy(
            Complaint.Priority.CRITICAL,
            response_hours=1,
            resolution_hours=6,
        )

        complaint = self.create_complaint(
            priority=Complaint.Priority.CRITICAL,
        )

        sla = create_complaint_sla(complaint)

        self.assertEqual(sla.policy, policy)

    def test_missing_policy_raises_sla_error(self):
        complaint = self.create_complaint(
            priority=Complaint.Priority.HIGH,
        )

        with self.assertRaises(SLAError):
            create_complaint_sla(complaint)

        self.assertFalse(
            ComplaintSLA.objects.filter(
                complaint=complaint,
            ).exists()
        )

    def test_inactive_policy_is_not_used(self):
        SLAPolicy.objects.create(
            priority=Complaint.Priority.HIGH,
            response_time_hours=2,
            resolution_time_hours=12,
            is_active=False,
        )

        complaint = self.create_complaint(
            priority=Complaint.Priority.HIGH,
        )

        with self.assertRaises(SLAError):
            create_complaint_sla(complaint)

        self.assertFalse(
            ComplaintSLA.objects.filter(
                complaint=complaint,
            ).exists()
        )

    def test_sla_creation_is_idempotent(self):
        policy = self.create_policy(
            Complaint.Priority.MEDIUM,
            response_hours=4,
            resolution_hours=24,
        )

        complaint = self.create_complaint(
            priority=Complaint.Priority.MEDIUM,
        )

        first_sla = create_complaint_sla(complaint)

        first_response_deadline = first_sla.response_deadline
        first_resolution_deadline = first_sla.resolution_deadline

        second_sla = create_complaint_sla(complaint)

        self.assertEqual(first_sla.pk, second_sla.pk)
        self.assertEqual(
            ComplaintSLA.objects.filter(
                complaint=complaint,
            ).count(),
            1,
        )
        self.assertEqual(second_sla.policy, policy)
        self.assertEqual(
            second_sla.response_deadline,
            first_response_deadline,
        )
        self.assertEqual(
            second_sla.resolution_deadline,
            first_resolution_deadline,
        )


class SLAMonitoringTests(Day26TestBase):
    """
    Verify response/resolution breach detection and escalation.
    """

    def create_policy(self, priority):
        return SLAPolicy.objects.create(
            priority=priority,
            response_time_hours=4,
            resolution_time_hours=24,
            is_active=True,
        )

    def create_sla_for_complaint(self, complaint):
        self.create_policy(complaint.priority)
        return create_complaint_sla(complaint)

    def test_missing_sla_raises_monitoring_error(self):
        complaint = self.create_complaint()

        with self.assertRaises(SLAMonitoringError):
            check_complaint_sla(complaint)

    def test_no_breach_when_deadlines_are_in_future(self):
        complaint = self.create_complaint()
        sla = self.create_sla_for_complaint(complaint)

        result = check_complaint_sla(complaint)

        self.assertFalse(result["response_breached"])
        self.assertFalse(result["resolution_breached"])
        self.assertFalse(result["escalated"])

        sla.refresh_from_db()

        self.assertFalse(sla.response_breached)
        self.assertFalse(sla.resolution_breached)

    def test_response_sla_breach_is_recorded(self):
        complaint = self.create_complaint()
        sla = self.create_sla_for_complaint(complaint)

        sla.response_deadline = timezone.now() - timedelta(hours=1)
        sla.save(update_fields=["response_deadline"])

        result = check_complaint_sla(complaint)

        self.assertTrue(result["response_breached"])
        self.assertFalse(result["resolution_breached"])
        self.assertFalse(result["escalated"])

        sla.refresh_from_db()

        self.assertTrue(sla.response_breached)

    def test_resolution_sla_breach_escalates_active_complaint(self):
        complaint = self.create_complaint(
            status=Complaint.Status.IN_PROGRESS,
        )
        sla = self.create_sla_for_complaint(complaint)

        sla.resolution_deadline = timezone.now() - timedelta(hours=1)
        sla.save(update_fields=["resolution_deadline"])

        result = check_complaint_sla(complaint)

        complaint.refresh_from_db()
        sla.refresh_from_db()

        self.assertTrue(result["resolution_breached"])
        self.assertTrue(result["escalated"])
        self.assertTrue(sla.resolution_breached)
        self.assertEqual(
            complaint.status,
            Complaint.Status.ESCALATED,
        )

    def test_resolution_breach_creates_escalation_history(self):
        complaint = self.create_complaint(
            status=Complaint.Status.IN_PROGRESS,
        )
        sla = self.create_sla_for_complaint(complaint)

        sla.resolution_deadline = timezone.now() - timedelta(hours=1)
        sla.save(update_fields=["resolution_deadline"])

        check_complaint_sla(complaint)

        history = ComplaintHistory.objects.filter(
            complaint=complaint,
            new_status=Complaint.Status.ESCALATED,
        ).first()

        self.assertIsNotNone(history)
        self.assertEqual(
            history.old_status,
            Complaint.Status.IN_PROGRESS,
        )
        self.assertIsNone(history.changed_by)

    def test_completed_response_does_not_breach_response_sla(self):
        complaint = self.create_complaint()
        sla = self.create_sla_for_complaint(complaint)

        sla.response_deadline = timezone.now() - timedelta(hours=1)
        sla.response_completed_at = timezone.now()
        sla.save(
            update_fields=[
                "response_deadline",
                "response_completed_at",
            ]
        )

        result = check_complaint_sla(complaint)

        self.assertFalse(result["response_breached"])

    def test_completed_resolution_does_not_breach_resolution_sla(self):
        complaint = self.create_complaint(
            status=Complaint.Status.IN_PROGRESS,
        )
        sla = self.create_sla_for_complaint(complaint)

        sla.resolution_deadline = timezone.now() - timedelta(hours=1)
        sla.resolution_completed_at = timezone.now()
        sla.save(
            update_fields=[
                "resolution_deadline",
                "resolution_completed_at",
            ]
        )

        result = check_complaint_sla(complaint)

        self.assertFalse(result["resolution_breached"])
        self.assertFalse(result["escalated"])

    def test_terminal_complaint_is_not_escalated(self):
        policy = self.create_policy(
            Complaint.Priority.MEDIUM,
        )

        terminal_statuses = [
            Complaint.Status.RESOLVED,
            Complaint.Status.CLOSED,
            Complaint.Status.REJECTED,
            Complaint.Status.ESCALATED,
        ]

        for index, terminal_status in enumerate(terminal_statuses):
            complaint = self.create_complaint(
                title=f"Terminal complaint {index}",
                status=terminal_status,
            )

            sla = ComplaintSLA.objects.create(
                complaint=complaint,
                policy=policy,
                response_deadline=(
                    complaint.created_at
                    + timedelta(hours=4)
                ),
                resolution_deadline=(
                    complaint.created_at
                    + timedelta(hours=24)
                ),
            )

            sla.resolution_deadline = (
                timezone.now() - timedelta(hours=1)
            )
            sla.save(update_fields=["resolution_deadline"])

            result = check_complaint_sla(complaint)

            complaint.refresh_from_db()

            self.assertTrue(result["resolution_breached"])
            self.assertFalse(result["escalated"])
            self.assertEqual(
                complaint.status,
                terminal_status,
            )


class AssignmentAndSLAMIntegrationTests(Day26TestBase):
    """
    Verify the complete Day 26 flow across assignment and SLA creation.
    """

    def test_assigned_complaint_can_have_sla_created_after_assignment(self):
        complaint = self.create_complaint(
            priority=Complaint.Priority.HIGH,
        )
        self.create_analysis(complaint)

        self.create_officer(
            email="officer.day26.integration@example.com",
        )

        assignment = assign_complaint(complaint)

        policy = SLAPolicy.objects.create(
            priority=Complaint.Priority.HIGH,
            response_time_hours=2,
            resolution_time_hours=12,
            is_active=True,
        )

        sla = create_complaint_sla(complaint)

        self.assertEqual(
            assignment.department,
            self.department,
        )
        self.assertEqual(
            complaint.status,
            Complaint.Status.ASSIGNED,
        )
        self.assertEqual(
            sla.policy,
            policy,
        )

    def test_failed_assignment_does_not_create_sla_automatically(self):
        complaint = self.create_complaint()
        self.create_analysis(complaint)

        with self.assertRaises(ComplaintAssignmentError):
            assign_complaint(complaint)

        self.assertFalse(
            ComplaintAssignment.objects.filter(
                complaint=complaint,
            ).exists()
        )

        self.assertFalse(
            ComplaintSLA.objects.filter(
                complaint=complaint,
            ).exists()
        )

    def test_assignment_preserves_complaint_priority_for_sla(self):
        complaint = self.create_complaint(
            priority=Complaint.Priority.CRITICAL,
        )
        self.create_analysis(
            complaint,
            priority=Complaint.Priority.CRITICAL,
        )

        self.create_officer(
            email="critical.officer.day26@example.com",
        )

        assign_complaint(complaint)

        SLAPolicy.objects.create(
            priority=Complaint.Priority.CRITICAL,
            response_time_hours=1,
            resolution_time_hours=6,
            is_active=True,
        )

        sla = create_complaint_sla(complaint)

        self.assertEqual(
            complaint.priority,
            Complaint.Priority.CRITICAL,
        )
        self.assertEqual(
            sla.policy.priority,
            Complaint.Priority.CRITICAL,
        )