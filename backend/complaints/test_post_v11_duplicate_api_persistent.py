from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from complaints.models import Complaint, ComplaintDuplicate
from organizations.models import Category, Department


User = get_user_model()


class PersistentDuplicateAPITests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(
            name="Water Department",
            is_active=True,
        )

        cls.category = Category.objects.create(
            name="Water Supply",
            department=cls.department,
            is_active=True,
        )

        cls.citizen = User.objects.create_user(
            email="citizen.duplicate.api@example.com",
            password="TestPass123!",
            role=User.Role.USER,
        )

        cls.other_citizen = User.objects.create_user(
            email="other.citizen.duplicate.api@example.com",
            password="TestPass123!",
            role=User.Role.USER,
        )

        cls.officer = User.objects.create_user(
            email="officer.duplicate.api@example.com",
            password="TestPass123!",
            role=User.Role.OFFICER,
            department=cls.department,
        )

        cls.other_officer_department = Department.objects.create(
            name="Roads Department",
            is_active=True,
        )

        cls.other_officer = User.objects.create_user(
            email="other.officer.duplicate.api@example.com",
            password="TestPass123!",
            role=User.Role.OFFICER,
            department=cls.other_officer_department,
        )

        cls.admin = User.objects.create_superuser(
            email="admin.duplicate.api@example.com",
            password="TestPass123!",
            role=User.Role.ADMIN,
        )

    @classmethod
    def create_complaint(
        cls,
        user,
        title,
        description,
    ):
        return Complaint.objects.create(
            user=user,
            category=cls.category,
            title=title,
            description=description,
            status=Complaint.Status.SUBMITTED,
        )

    @classmethod
    def create_duplicate(
        cls,
        complaint,
        possible_duplicate,
    ):
        return ComplaintDuplicate.objects.create(
            complaint=complaint,
            possible_duplicate=possible_duplicate,
            similarity_score=Decimal("0.92345"),
            detection_threshold=Decimal("0.85000"),
            embedding_model="gemini-embedding-001",
        )

    def test_citizen_can_list_own_persistent_duplicates(self):
        complaint = self.create_complaint(
            self.citizen,
            "Water leakage",
            "Water is leaking near the main road.",
        )

        possible_duplicate = self.create_complaint(
            self.other_citizen,
            "Water pipe leakage",
            "A water pipe is leaking near the main road.",
        )

        self.create_duplicate(
            complaint,
            possible_duplicate,
        )

        self.client.force_authenticate(
            user=self.citizen,
        )

        url = reverse(
            "complaint-duplicate-list",
        )

        response = self.client.get(
            url,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["similarity_score"],
            "0.92345",
        )

    def test_citizen_cannot_see_other_citizens_duplicates(self):
        complaint = self.create_complaint(
            self.other_citizen,
            "Water shortage",
            "There is no water supply.",
        )

        possible_duplicate = self.create_complaint(
            self.citizen,
            "Water problem",
            "Water supply is unavailable.",
        )

        self.create_duplicate(
            complaint,
            possible_duplicate,
        )

        self.client.force_authenticate(
            user=self.citizen,
        )

        url = reverse(
            "complaint-duplicate-list",
        )

        response = self.client.get(
            url,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data,
            [],
        )

    def test_officer_can_see_duplicates_for_assigned_complaint(self):
        complaint = self.create_complaint(
            self.citizen,
            "Water leakage",
            "Water is leaking from a pipeline.",
        )

        possible_duplicate = self.create_complaint(
            self.other_citizen,
            "Pipeline leak",
            "There is a pipeline leakage.",
        )

        from complaints.models import ComplaintAssignment

        ComplaintAssignment.objects.create(
            complaint=complaint,
            department=self.department,
            officer=self.officer,
            assigned_by=self.admin,
        )

        self.create_duplicate(
            complaint,
            possible_duplicate,
        )

        self.client.force_authenticate(
            user=self.officer,
        )

        url = reverse(
            "complaint-duplicate-list",
        )

        response = self.client.get(
            url,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

    def test_unrelated_officer_cannot_see_duplicates(self):
        complaint = self.create_complaint(
            self.citizen,
            "Water leakage",
            "Water is leaking from a pipeline.",
        )

        possible_duplicate = self.create_complaint(
            self.other_citizen,
            "Pipeline leak",
            "There is a pipeline leakage.",
        )

        from complaints.models import ComplaintAssignment

        ComplaintAssignment.objects.create(
            complaint=complaint,
            department=self.department,
            officer=self.officer,
            assigned_by=self.admin,
        )

        self.create_duplicate(
            complaint,
            possible_duplicate,
        )

        self.client.force_authenticate(
            user=self.other_officer,
        )

        url = reverse(
            "complaint-duplicate-list",
        )

        response = self.client.get(
            url,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data,
            [],
        )

    def test_admin_can_list_all_duplicate_records(self):
        complaint = self.create_complaint(
            self.citizen,
            "Water complaint",
            "Water supply is interrupted.",
        )

        possible_duplicate = self.create_complaint(
            self.other_citizen,
            "Water issue",
            "Water supply is not available.",
        )

        self.create_duplicate(
            complaint,
            possible_duplicate,
        )

        self.client.force_authenticate(
            user=self.admin,
        )

        url = reverse(
            "complaint-duplicate-list",
        )

        response = self.client.get(
            url,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertGreaterEqual(
            len(response.data),
            1,
        )

    def test_admin_can_confirm_duplicate(self):
        complaint = self.create_complaint(
            self.citizen,
            "Street water leak",
            "Water is leaking on the street.",
        )

        possible_duplicate = self.create_complaint(
            self.other_citizen,
            "Water leakage",
            "There is a water leak on the street.",
        )

        duplicate = self.create_duplicate(
            complaint,
            possible_duplicate,
        )

        self.client.force_authenticate(
            user=self.admin,
        )

        url = reverse(
            "complaint-duplicate-detail",
            kwargs={"pk": duplicate.id},
        )

        response = self.client.patch(
            url,
            {
                "status": ComplaintDuplicate.Status.CONFIRMED,
                "review_comment": (
                    "Both complaints describe "
                    "the same water leakage."
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        duplicate.refresh_from_db()

        self.assertEqual(
            duplicate.status,
            ComplaintDuplicate.Status.CONFIRMED,
        )

        self.assertEqual(
            duplicate.reviewed_by,
            self.admin,
        )

        self.assertIsNotNone(
            duplicate.reviewed_at,
        )

        self.assertEqual(
            duplicate.review_comment,
            "Both complaints describe the same water leakage.",
        )

    def test_admin_can_reject_duplicate(self):
        complaint = self.create_complaint(
            self.citizen,
            "Water complaint",
            "Water supply is low.",
        )

        possible_duplicate = self.create_complaint(
            self.other_citizen,
            "Different water issue",
            "Water pressure is low in another location.",
        )

        duplicate = self.create_duplicate(
            complaint,
            possible_duplicate,
        )

        self.client.force_authenticate(
            user=self.admin,
        )

        url = reverse(
            "complaint-duplicate-detail",
            kwargs={"pk": duplicate.id},
        )

        response = self.client.patch(
            url,
            {
                "status": ComplaintDuplicate.Status.REJECTED,
                "review_comment": "Different locations.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        duplicate.refresh_from_db()

        self.assertEqual(
            duplicate.status,
            ComplaintDuplicate.Status.REJECTED,
        )

        self.assertEqual(
            duplicate.reviewed_by,
            self.admin,
        )

        self.assertIsNotNone(
            duplicate.reviewed_at,
        )

    def test_non_admin_cannot_review_duplicate(self):
        complaint = self.create_complaint(
            self.citizen,
            "Water complaint",
            "There is a water issue.",
        )

        possible_duplicate = self.create_complaint(
            self.other_citizen,
            "Water issue",
            "There is another water issue.",
        )

        duplicate = self.create_duplicate(
            complaint,
            possible_duplicate,
        )

        self.client.force_authenticate(
            user=self.citizen,
        )

        url = reverse(
            "complaint-duplicate-detail",
            kwargs={"pk": duplicate.id},
        )

        response = self.client.patch(
            url,
            {
                "status": ComplaintDuplicate.Status.CONFIRMED,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        duplicate.refresh_from_db()

        self.assertEqual(
            duplicate.status,
            ComplaintDuplicate.Status.PENDING,
        )

    def test_invalid_review_status_is_rejected(self):
        complaint = self.create_complaint(
            self.citizen,
            "Water issue",
            "There is a water issue.",
        )

        possible_duplicate = self.create_complaint(
            self.other_citizen,
            "Water problem",
            "There is a water problem.",
        )

        duplicate = self.create_duplicate(
            complaint,
            possible_duplicate,
        )

        self.client.force_authenticate(
            user=self.admin,
        )

        url = reverse(
            "complaint-duplicate-detail",
            kwargs={"pk": duplicate.id},
        )

        response = self.client.patch(
            url,
            {
                "status": "INVALID",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        duplicate.refresh_from_db()

        self.assertEqual(
            duplicate.status,
            ComplaintDuplicate.Status.PENDING,
        )

    def test_duplicate_records_cannot_be_manually_created(self):
        self.client.force_authenticate(
            user=self.admin,
        )

        url = reverse(
            "complaint-duplicate-list",
        )

        response = self.client.post(
            url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    def test_duplicate_records_cannot_be_deleted(self):
        complaint = self.create_complaint(
            self.citizen,
            "Water issue",
            "There is a water issue.",
        )

        possible_duplicate = self.create_complaint(
            self.other_citizen,
            "Water problem",
            "There is a water problem.",
        )

        duplicate = self.create_duplicate(
            complaint,
            possible_duplicate,
        )

        self.client.force_authenticate(
            user=self.admin,
        )

        url = reverse(
            "complaint-duplicate-detail",
            kwargs={"pk": duplicate.id},
        )

        response = self.client.delete(
            url,
        )

        self.assertEqual(
            response.status_code,
            405,
        )

        self.assertTrue(
            ComplaintDuplicate.objects.filter(
                pk=duplicate.id,
            ).exists()
        )
