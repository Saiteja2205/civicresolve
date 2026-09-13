from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from complaints.models import (
    Complaint,
    ComplaintAssignment,
    ComplaintDuplicate,
)
from organizations.models import Category, Department


class DuplicateDetectionAPITests(APITestCase):

    def setUp(self):
        self.password = "TestPassword123!"

        self.department = Department.objects.create(
            name="Sanitation",
            description="Sanitation department",
            is_active=True,
        )

        self.category = Category.objects.create(
            name="Garbage Collection",
            description="Garbage collection complaints",
            department=self.department,
            is_active=True,
        )

        self.other_department = Department.objects.create(
            name="Water Supply",
            description="Water supply department",
            is_active=True,
        )

        self.other_category = Category.objects.create(
            name="Water Leakage",
            description="Water leakage complaints",
            department=self.other_department,
            is_active=True,
        )

        self.citizen = User.objects.create_user(
            email="citizen.duplicate.api@example.com",
            password=self.password,
            first_name="Duplicate",
            last_name="Citizen",
            role=User.Role.USER,
        )

        self.other_citizen = User.objects.create_user(
            email="other.duplicate.api@example.com",
            password=self.password,
            first_name="Other",
            last_name="Citizen",
            role=User.Role.USER,
        )

        self.officer = User.objects.create_user(
            email="officer.duplicate.api@example.com",
            password=self.password,
            first_name="Duplicate",
            last_name="Officer",
            role=User.Role.OFFICER,
            department=self.department,
        )

        self.other_officer = User.objects.create_user(
            email="other.officer.duplicate.api@example.com",
            password=self.password,
            first_name="Other",
            last_name="Officer",
            role=User.Role.OFFICER,
            department=self.other_department,
        )

        self.admin = User.objects.create_superuser(
            email="admin.duplicate.api@example.com",
            password=self.password,
            first_name="Duplicate",
            last_name="Admin",
            role=User.Role.ADMIN,
        )

        self.complaint = Complaint.objects.create(
            user=self.citizen,
            category=self.category,
            title="Garbage collection missed",
            description=(
                "Garbage has not been collected "
                "from our street."
            ),
            status=Complaint.Status.SUBMITTED,
            priority=Complaint.Priority.MEDIUM,
            location="Hyderabad",
        )

        self.similar_complaint = Complaint.objects.create(
            user=self.other_citizen,
            category=self.category,
            title="Garbage truck not visiting",
            description=(
                "The garbage vehicle has not "
                "visited our road."
            ),
            status=Complaint.Status.SUBMITTED,
            priority=Complaint.Priority.MEDIUM,
            location="Hyderabad",
        )

        self.url = reverse(
            "complaint-duplicates",
            kwargs={
                "pk": self.complaint.id,
            },
        )

        self.duplicate_list_url = reverse(
            "complaint-duplicate-list",
        )

    def create_duplicate(
        self,
        *,
        complaint=None,
        possible_duplicate=None,
        similarity_score=0.9174,
        detection_threshold=0.85,
        status_value=ComplaintDuplicate.Status.PENDING,
    ):
        return ComplaintDuplicate.objects.create(
            complaint=complaint or self.complaint,
            possible_duplicate=(
                possible_duplicate or self.similar_complaint
            ),
            similarity_score=similarity_score,
            detection_threshold=detection_threshold,
            status=status_value,
        )

    def test_admin_can_access_duplicates(self):
        duplicate = self.create_duplicate()

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["complaint_id"],
            self.complaint.id,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        result = response.data["results"][0]

        self.assertEqual(
            result["possible_duplicate_ticket_number"],
            duplicate.possible_duplicate.ticket_number,
        )

        self.assertEqual(
            result["similarity_percentage"],
            91.74,
        )

        self.assertEqual(
            result["status"],
            ComplaintDuplicate.Status.PENDING,
        )

    def test_citizen_can_access_own_complaint_duplicates(self):
        self.create_duplicate()

        self.client.force_authenticate(
            user=self.citizen
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["possible_duplicate_ticket_number"],
            self.similar_complaint.ticket_number,
        )

    def test_citizen_cannot_access_other_users_complaint(self):
        self.create_duplicate()

        self.client.force_authenticate(
            user=self.other_citizen
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_officer_can_access_assigned_complaint(self):
        self.create_duplicate()

        ComplaintAssignment.objects.create(
            complaint=self.complaint,
            department=self.department,
            officer=self.officer,
            assigned_by=self.admin,
            reason="Test assignment.",
        )

        self.client.force_authenticate(
            user=self.officer
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

    def test_unassigned_officer_cannot_access_complaint(self):
        self.create_duplicate()

        self.client.force_authenticate(
            user=self.officer
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_unrelated_officer_cannot_access_complaint(self):
        self.create_duplicate()

        ComplaintAssignment.objects.create(
            complaint=self.complaint,
            department=self.department,
            officer=self.officer,
            assigned_by=self.admin,
            reason="Test assignment.",
        )

        self.client.force_authenticate(
            user=self.other_officer
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_unauthenticated_user_cannot_access_duplicates(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_duplicate_endpoint_returns_persisted_records(self):
        duplicate = self.create_duplicate(
            similarity_score=0.9012,
        )

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        result = response.data["results"][0]

        self.assertEqual(
            result["id"],
            duplicate.id,
        )

        self.assertEqual(
            result["possible_duplicate_ticket_number"],
            self.similar_complaint.ticket_number,
        )

        self.assertEqual(
            result["similarity_percentage"],
            90.12,
        )

    def test_duplicate_endpoint_returns_empty_results_when_no_records_exist(
        self,
    ):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["complaint_id"],
            self.complaint.id,
        )

        self.assertEqual(
            response.data["ticket_number"],
            self.complaint.ticket_number,
        )

        self.assertEqual(
            response.data["count"],
            0,
        )

        self.assertEqual(
            response.data["results"],
            [],
        )

    def test_duplicate_list_endpoint_can_be_used_by_admin(self):
        duplicate = self.create_duplicate()

        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            self.duplicate_list_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIsInstance(
            response.data,
            list,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["id"],
            duplicate.id,
        )

    def test_duplicate_list_endpoint_does_not_allow_direct_creation(
        self,
    ):
        self.client.force_authenticate(
            user=self.admin
        )

        payload = {
            "complaint": self.complaint.id,
            "possible_duplicate": self.similar_complaint.id,
            "similarity_score": 0.92,
        }

        response = self.client.post(
            self.duplicate_list_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

        self.assertEqual(
            ComplaintDuplicate.objects.count(),
            0,
        )



