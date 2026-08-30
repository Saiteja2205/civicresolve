from django.contrib.auth import get_user_model
from django.test import TestCase

from complaints.models import Complaint
from complaints.services.complaint_service import (
    change_complaint_status,
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