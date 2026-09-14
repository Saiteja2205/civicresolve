from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from complaints.models import (
    Complaint,
    ComplaintAnalysis,
    ComplaintAssignment,
    ComplaintHistory,
    ComplaintSLA,
    SLAPolicy,
)
from complaints.services.sla_risk_service import (
    calculate_sla_risk,
)
from organizations.models import Category, Department


User = get_user_model()


class SLARiskServiceTests(TestCase):

    def setUp(self):
        self.department = Department.objects.create(
            name="Roads and Infrastructure Department"
        )

        self.category = Category.objects.create(
            name="Road Damage",
            department=self.department,
        )

        self.user = User.objects.create_user(
            email="risk-user@test.com",
            password="testpassword",
            role=User.Role.USER,
        )

        self.officer = User.objects.create_user(
            email="risk-officer@test.com",
            password="testpassword",
            role=User.Role.OFFICER,
            department=self.department,
            is_active=True,
        )

        self.complaint = Complaint.objects.create(
            user=self.user,
            category=self.category,
            title="Large pothole near school",
            description=(
                "A large pothole is creating a serious "
                "problem for vehicles."
            ),
            status=Complaint.Status.IN_PROGRESS,
            priority=Complaint.Priority.HIGH,
        )

        self.analysis = ComplaintAnalysis.objects.create(
            complaint=self.complaint,
            summary="Large pothole.",
            explanation=(
                "The complaint describes road damage."
            ),
            predicted_category=self.category,
            predicted_department=self.department,
            predicted_priority=Complaint.Priority.HIGH,
            urgency_score=75,
            confidence_score=95,
            model_name="test-model",
        )

        self.policy = SLAPolicy.objects.create(
            priority=Complaint.Priority.HIGH,
            response_time_hours=8,
            resolution_time_hours=24,
            is_active=True,
        )

        self.assignment = ComplaintAssignment.objects.create(
            complaint=self.complaint,
            department=self.department,
            officer=self.officer,
            assigned_by=self.officer,
            reason="Test assignment.",
        )

        now = timezone.now()

        self.sla = ComplaintSLA.objects.create(
            complaint=self.complaint,
            policy=self.policy,
            response_deadline=(
                now + timedelta(hours=2)
            ),
            resolution_deadline=(
                now + timedelta(hours=12)
            ),
        )

        ComplaintHistory.objects.create(
            complaint=self.complaint,
            changed_by=self.user,
            old_status="",
            new_status=Complaint.Status.SUBMITTED,
            comment="Complaint submitted.",
        )

        ComplaintHistory.objects.create(
            complaint=self.complaint,
            changed_by=self.officer,
            old_status=Complaint.Status.ASSIGNED,
            new_status=Complaint.Status.IN_PROGRESS,
            comment="Work started.",
        )

    def test_low_risk_when_deadlines_are_far_away(self):
        self.sla.response_deadline = (
            timezone.now()
            + timedelta(hours=7)
        )

        self.sla.resolution_deadline = (
            timezone.now()
            + timedelta(hours=23)
        )

        self.sla.save()

        self.complaint.priority = (
            Complaint.Priority.LOW
        )

        self.complaint.save()

        self.analysis.urgency_score = 10
        self.analysis.save()

        self.complaint.refresh_from_db()

        result = calculate_sla_risk(
            self.complaint
        )

        self.assertIn(
            result["risk_level"],
            {
                "LOW",
                "MEDIUM",
            },
        )

        self.assertGreaterEqual(
            result["risk_score"],
            0,
        )

    def test_high_risk_when_resolution_deadline_is_breached(self):
        now = timezone.now()

        self.sla.response_deadline = (
            now - timedelta(hours=1)
        )

        self.sla.resolution_deadline = (
            now - timedelta(hours=1)
        )

        self.sla.response_breached = False
        self.sla.resolution_breached = True

        self.sla.save()

        self.sla.refresh_from_db()
        self.complaint.refresh_from_db()

        result = calculate_sla_risk(
            self.complaint
        )

        self.assertIn(
            result["risk_level"],
            {
                "HIGH",
                "CRITICAL",
            },
        )

        self.assertGreaterEqual(
            result["risk_score"],
            70,
        )

        self.assertTrue(
            result["resolution_breached"]
        )

        self.assertTrue(
            any(
                "resolution sla"
                in factor.lower()
                for factor in result["factors"]
            )
        )

    def test_critical_risk_from_multiple_pressure_signals(self):
        now = timezone.now()

        self.sla.response_deadline = (
            now - timedelta(hours=1)
        )

        self.sla.resolution_deadline = (
            now - timedelta(hours=1)
        )

        self.sla.response_breached = True
        self.sla.resolution_breached = True

        self.sla.save()

        self.complaint.status = (
            Complaint.Status.ESCALATED
        )

        self.complaint.save()

        self.analysis.urgency_score = 95
        self.analysis.save()

        self.sla.refresh_from_db()
        self.complaint.refresh_from_db()

        result = calculate_sla_risk(
            self.complaint
        )

        self.assertEqual(
            result["risk_level"],
            "CRITICAL",
        )

        self.assertEqual(
            result["risk_score"],
            100,
        )

    def test_terminal_complaint_has_no_active_risk(self):
        self.complaint.status = (
            Complaint.Status.RESOLVED
        )

        self.complaint.save()

        self.complaint.refresh_from_db()

        result = calculate_sla_risk(
            self.complaint
        )

        self.assertEqual(
            result["risk_score"],
            0,
        )

        self.assertEqual(
            result["risk_level"],
            "LOW",
        )


class SLARiskAPITests(TestCase):

    def setUp(self):
        self.department = Department.objects.create(
            name="Water Supply Department"
        )

        self.category = Category.objects.create(
            name="Water Leakage",
            department=self.department,
        )

        self.user = User.objects.create_user(
            email="api-risk-user@test.com",
            password="testpassword",
            role=User.Role.USER,
        )

        self.other_user = User.objects.create_user(
            email="other-risk-user@test.com",
            password="testpassword",
            role=User.Role.USER,
        )

        self.officer = User.objects.create_user(
            email="api-risk-officer@test.com",
            password="testpassword",
            role=User.Role.OFFICER,
            department=self.department,
            is_active=True,
        )

        self.admin = User.objects.create_user(
            email="api-risk-admin@test.com",
            password="testpassword",
            role=User.Role.ADMIN,
        )

        self.complaint = Complaint.objects.create(
            user=self.user,
            category=self.category,
            title="Water leakage",
            description=(
                "Water is leaking from the main pipe."
            ),
            status=Complaint.Status.ASSIGNED,
            priority=Complaint.Priority.MEDIUM,
        )

        policy = SLAPolicy.objects.create(
            priority=Complaint.Priority.MEDIUM,
            response_time_hours=24,
            resolution_time_hours=72,
            is_active=True,
        )

        ComplaintAssignment.objects.create(
            complaint=self.complaint,
            department=self.department,
            officer=self.officer,
            assigned_by=self.admin,
            reason="Test assignment.",
        )

        ComplaintSLA.objects.create(
            complaint=self.complaint,
            policy=policy,
            response_deadline=(
                timezone.now()
                + timedelta(hours=12)
            ),
            resolution_deadline=(
                timezone.now()
                + timedelta(hours=48)
            ),
        )

        ComplaintHistory.objects.create(
            complaint=self.complaint,
            changed_by=self.user,
            old_status="",
            new_status=Complaint.Status.SUBMITTED,
            comment="Complaint submitted.",
        )

        self.client = APIClient()

    def test_owner_can_view_sla_risk(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            f"/api/complaints/{self.complaint.id}/sla-risk/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "risk_score",
            response.data,
        )

        self.assertIn(
            "risk_level",
            response.data,
        )

        self.assertIn(
            "factors",
            response.data,
        )

    def test_other_citizen_cannot_view_sla_risk(self):
        self.client.force_authenticate(
            user=self.other_user
        )

        response = self.client.get(
            f"/api/complaints/{self.complaint.id}/sla-risk/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_assigned_officer_can_view_sla_risk(self):
        self.client.force_authenticate(
            user=self.officer
        )

        response = self.client.get(
            f"/api/complaints/{self.complaint.id}/sla-risk/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_admin_can_view_sla_risk(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            f"/api/complaints/{self.complaint.id}/sla-risk/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )