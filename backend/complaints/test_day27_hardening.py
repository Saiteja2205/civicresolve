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
from complaints.services.ai_orchestration_service import (
    run_ai_analysis,
)
from complaints.services.ai_provider import (
    AIProviderError,
)
from complaints.services.assignment_service import (
    ComplaintAssignmentError,
    assign_complaint,
)
from complaints.services.sla_monitoring_service import (
    check_complaint_sla,
)
from complaints.services.sla_service import (
    SLAError,
    create_complaint_sla,
)
from organizations.models import Category, Department


User = get_user_model()


class Day27BaseTestCase(TestCase):
    """
    Shared test setup for Day 27 backend hardening.
    """

    def setUp(self):
        self.department = Department.objects.create(
            name="Day27 IT Department",
            is_active=True,
        )

        self.category = Category.objects.create(
            name="Day27 Network Issues",
            department=self.department,
            is_active=True,
        )

        self.user = User.objects.create_user(
            email="day27.user@example.com",
            password="TestPass123!",
            role=User.Role.USER,
        )

        self.system_user = User.objects.create_user(
            email="system@civicresolve.local",
            password="SystemPass123!",
            role=User.Role.ADMIN,
            is_active=True,
        )

    def create_complaint(
        self,
        *,
        status=Complaint.Status.AI_ANALYZING,
        priority=Complaint.Priority.MEDIUM,
        title="Day 27 complaint",
    ):
        return Complaint.objects.create(
            user=self.user,
            category=self.category,
            title=title,
            description="A complaint used for Day 27 testing.",
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
            summary="Day 27 AI summary.",
            explanation="Day 27 AI explanation.",
            predicted_category=category or self.category,
            predicted_department=department or self.department,
            predicted_priority=priority or complaint.priority,
            urgency_score="75.00",
            confidence_score="95.00",
            model_name="Day27-Test-Model",
        )

    def create_policy(
        self,
        priority=Complaint.Priority.MEDIUM,
        response_hours=4,
        resolution_hours=24,
    ):
        return SLAPolicy.objects.create(
            priority=priority,
            response_time_hours=response_hours,
            resolution_time_hours=resolution_hours,
            is_active=True,
        )


class AIOrchestrationHardeningTests(Day27BaseTestCase):
    """
    Verify AI workflow success and failure boundaries.
    """

    def test_ai_success_keeps_complaint_in_ai_analyzing(self):
        complaint = self.create_complaint(
            status=Complaint.Status.SUBMITTED,
        )

        with patch(
            "complaints.services.ai_analysis_service.GeminiProvider"
        ) as provider_class:
            provider = provider_class.return_value
            provider.model_name = "Day27-Test-Model"

            provider.analyze_complaint.return_value = (
                '{"summary": "Network service interruption.",'
                '"explanation": "The complaint describes a network outage.",'
                f'"predicted_category": {self.category.id},'
                f'"predicted_department": {self.department.id},'
                '"predicted_priority": "HIGH",'
                '"urgency_score": 80,'
                '"confidence_score": 96}'
            )

            result = run_ai_analysis(complaint)

        complaint.refresh_from_db()

        self.assertTrue(result["success"])
        self.assertIsNotNone(result["analysis"])
        self.assertIsNone(result["error"])

        self.assertEqual(
            complaint.status,
            Complaint.Status.AI_ANALYZING,
        )

        self.assertTrue(
            ComplaintAnalysis.objects.filter(
                complaint=complaint,
            ).exists()
        )

        self.assertEqual(
            complaint.priority,
            Complaint.Priority.HIGH,
        )

    def test_ai_provider_failure_returns_complaint_to_submitted(self):
        complaint = self.create_complaint(
            status=Complaint.Status.SUBMITTED,
        )

        with patch(
            "complaints.services.ai_analysis_service.GeminiProvider"
        ) as provider_class:
            provider = provider_class.return_value

            provider.analyze_complaint.side_effect = AIProviderError(
                "Simulated AI provider failure."
            )

            result = run_ai_analysis(complaint)

        complaint.refresh_from_db()

        self.assertFalse(result["success"])
        self.assertIsNone(result["analysis"])
        self.assertIn(
            "Simulated AI provider failure.",
            result["error"],
        )

        self.assertEqual(
            complaint.status,
            Complaint.Status.SUBMITTED,
        )

        self.assertFalse(
            ComplaintAnalysis.objects.filter(
                complaint=complaint,
            ).exists()
        )

    def test_ai_provider_failure_creates_recovery_history(self):
        complaint = self.create_complaint(
            status=Complaint.Status.SUBMITTED,
        )

        with patch(
            "complaints.services.ai_analysis_service.GeminiProvider"
        ) as provider_class:
            provider = provider_class.return_value

            provider.analyze_complaint.side_effect = AIProviderError(
                "AI unavailable."
            )

            run_ai_analysis(complaint)

        history = ComplaintHistory.objects.filter(
            complaint=complaint,
        ).order_by("id")

        self.assertEqual(history.count(), 2)

        self.assertEqual(
            history[0].old_status,
            Complaint.Status.SUBMITTED,
        )

        self.assertEqual(
            history[0].new_status,
            Complaint.Status.AI_ANALYZING,
        )

        self.assertEqual(
            history[1].old_status,
            Complaint.Status.AI_ANALYZING,
        )

        self.assertEqual(
            history[1].new_status,
            Complaint.Status.SUBMITTED,
        )

    def test_invalid_ai_output_is_converted_to_provider_error(self):
        complaint = self.create_complaint(
            status=Complaint.Status.SUBMITTED,
        )

        with patch(
            "complaints.services.ai_analysis_service.GeminiProvider"
        ) as provider_class:
            provider = provider_class.return_value

            provider.analyze_complaint.return_value = (
                '{"summary": "Invalid output.",'
                '"explanation": "Invalid priority.",'
                f'"predicted_category": {self.category.id},'
                f'"predicted_department": {self.department.id},'
                '"predicted_priority": "NOT_A_PRIORITY",'
                '"urgency_score": 50,'
                '"confidence_score": 90}'
            )

            result = run_ai_analysis(complaint)

        complaint.refresh_from_db()

        self.assertFalse(result["success"])
        self.assertIsNone(result["analysis"])

        self.assertIn(
            "AI output validation failed",
            result["error"],
        )

        self.assertEqual(
            complaint.status,
            Complaint.Status.SUBMITTED,
        )


class SLABreachHardeningTests(Day27BaseTestCase):
    """
    Verify repeated SLA checks and escalation behavior.
    """

    def test_repeated_resolution_breach_does_not_duplicate_escalation(
        self,
    ):
        complaint = self.create_complaint(
            status=Complaint.Status.IN_PROGRESS,
        )

        self.create_policy(
            priority=complaint.priority,
            response_hours=4,
            resolution_hours=24,
        )

        sla = create_complaint_sla(complaint)

        sla.resolution_deadline = (
            timezone.now() - timedelta(hours=1)
        )

        sla.save(
            update_fields=["resolution_deadline"]
        )

        first_result = check_complaint_sla(complaint)

        complaint.refresh_from_db()

        second_result = check_complaint_sla(complaint)

        complaint.refresh_from_db()

        escalation_history = ComplaintHistory.objects.filter(
            complaint=complaint,
            new_status=Complaint.Status.ESCALATED,
        )

        self.assertTrue(first_result["escalated"])
        self.assertFalse(second_result["escalated"])

        self.assertEqual(
            escalation_history.count(),
            1,
        )

        self.assertEqual(
            complaint.status,
            Complaint.Status.ESCALATED,
        )

    def test_repeated_response_breach_remains_recorded(self):
        complaint = self.create_complaint()

        self.create_policy(
            priority=complaint.priority,
            response_hours=4,
            resolution_hours=24,
        )

        sla = create_complaint_sla(complaint)

        sla.response_deadline = (
            timezone.now() - timedelta(hours=1)
        )

        sla.save(
            update_fields=["response_deadline"]
        )

        first_result = check_complaint_sla(complaint)
        second_result = check_complaint_sla(complaint)

        sla.refresh_from_db()

        self.assertTrue(first_result["response_breached"])
        self.assertTrue(second_result["response_breached"])
        self.assertTrue(sla.response_breached)

    def test_response_breach_does_not_escalate_by_itself(self):
        complaint = self.create_complaint(
            status=Complaint.Status.IN_PROGRESS,
        )

        self.create_policy(
            priority=complaint.priority,
            response_hours=4,
            resolution_hours=24,
        )

        sla = create_complaint_sla(complaint)

        sla.response_deadline = (
            timezone.now() - timedelta(hours=1)
        )

        sla.save(
            update_fields=["response_deadline"]
        )

        result = check_complaint_sla(complaint)

        complaint.refresh_from_db()

        self.assertTrue(result["response_breached"])
        self.assertFalse(result["resolution_breached"])
        self.assertFalse(result["escalated"])

        self.assertEqual(
            complaint.status,
            Complaint.Status.IN_PROGRESS,
        )

    def test_resolution_breach_escalation_records_system_generated_history(
        self,
    ):
        complaint = self.create_complaint(
            status=Complaint.Status.IN_PROGRESS,
        )

        self.create_policy(
            priority=complaint.priority,
            response_hours=4,
            resolution_hours=24,
        )

        sla = create_complaint_sla(complaint)

        sla.resolution_deadline = (
            timezone.now() - timedelta(hours=1)
        )

        sla.save(
            update_fields=["resolution_deadline"]
        )

        check_complaint_sla(complaint)

        history = ComplaintHistory.objects.filter(
            complaint=complaint,
            new_status=Complaint.Status.ESCALATED,
        ).first()

        self.assertIsNotNone(history)
        self.assertIsNone(history.changed_by)

        self.assertIn(
            "automatically escalated",
            history.comment.lower(),
        )


class TransactionHardeningTests(Day27BaseTestCase):
    """
    Verify that failed multi-step operations do not leave
    partial database state.
    """

    def test_assignment_failure_does_not_create_partial_assignment(
        self,
    ):
        complaint = self.create_complaint()
        self.create_analysis(complaint)

        with self.assertRaises(ComplaintAssignmentError):
            assign_complaint(complaint)

        complaint.refresh_from_db()

        self.assertEqual(
            complaint.status,
            Complaint.Status.AI_ANALYZING,
        )

        self.assertEqual(
            ComplaintAssignment.objects.filter(
                complaint=complaint,
            ).count(),
            0,
        )

    def test_assignment_failure_does_not_create_history(self):
        complaint = self.create_complaint()
        self.create_analysis(complaint)

        initial_history_count = ComplaintHistory.objects.filter(
            complaint=complaint,
        ).count()

        with self.assertRaises(ComplaintAssignmentError):
            assign_complaint(complaint)

        final_history_count = ComplaintHistory.objects.filter(
            complaint=complaint,
        ).count()

        self.assertEqual(
            final_history_count,
            initial_history_count,
        )

    def test_sla_creation_uses_complaint_priority_after_ai_update(
        self,
    ):
        complaint = self.create_complaint(
            priority=Complaint.Priority.MEDIUM,
        )

        complaint.priority = Complaint.Priority.CRITICAL

        complaint.save(
            update_fields=[
                "priority",
                "updated_at",
            ]
        )

        critical_policy = self.create_policy(
            priority=Complaint.Priority.CRITICAL,
            response_hours=1,
            resolution_hours=6,
        )

        sla = create_complaint_sla(complaint)

        self.assertEqual(
            sla.policy,
            critical_policy,
        )

        self.assertEqual(
            sla.policy.priority,
            Complaint.Priority.CRITICAL,
        )


class CompleteWorkflowHardeningTests(Day27BaseTestCase):
    """
    Verify important backend workflow boundaries together.
    """

    def test_successful_assignment_followed_by_sla_creation(self):
        complaint = self.create_complaint(
            status=Complaint.Status.AI_ANALYZING,
            priority=Complaint.Priority.HIGH,
        )

        self.create_analysis(
            complaint,
            priority=Complaint.Priority.HIGH,
        )

        User.objects.create_user(
            email="day27.officer@example.com",
            password="TestPass123!",
            role=User.Role.OFFICER,
            department=self.department,
            is_active=True,
        )

        policy = self.create_policy(
            priority=Complaint.Priority.HIGH,
            response_hours=2,
            resolution_hours=12,
        )

        assignment = assign_complaint(complaint)

        complaint.refresh_from_db()

        sla = create_complaint_sla(complaint)

        self.assertEqual(
            complaint.status,
            Complaint.Status.ASSIGNED,
        )

        self.assertEqual(
            assignment.department,
            self.department,
        )

        self.assertEqual(
            assignment.officer.department,
            self.department,
        )

        self.assertEqual(
            sla.policy,
            policy,
        )

    def test_escalation_after_assignment_and_sla_creation(self):
        complaint = self.create_complaint(
            status=Complaint.Status.AI_ANALYZING,
            priority=Complaint.Priority.HIGH,
        )

        self.create_analysis(
            complaint,
            priority=Complaint.Priority.HIGH,
        )

        User.objects.create_user(
            email="day27.escalation.officer@example.com",
            password="TestPass123!",
            role=User.Role.OFFICER,
            department=self.department,
            is_active=True,
        )

        self.create_policy(
            priority=Complaint.Priority.HIGH,
            response_hours=2,
            resolution_hours=12,
        )

        assign_complaint(complaint)

        complaint.refresh_from_db()

        sla = create_complaint_sla(complaint)

        sla.resolution_deadline = (
            timezone.now() - timedelta(hours=1)
        )

        sla.save(
            update_fields=["resolution_deadline"]
        )

        complaint.status = Complaint.Status.IN_PROGRESS

        complaint.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        result = check_complaint_sla(complaint)

        complaint.refresh_from_db()

        self.assertTrue(result["resolution_breached"])
        self.assertTrue(result["escalated"])

        self.assertEqual(
            complaint.status,
            Complaint.Status.ESCALATED,
        )

        self.assertTrue(
            ComplaintSLA.objects.filter(
                complaint=complaint,
                resolution_breached=True,
            ).exists()
        )