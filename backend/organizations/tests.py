from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from organizations.models import Category, Department


User = get_user_model()


class OrganizationAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.department = Department.objects.create(
            name="Public Works",
            description="Handles public infrastructure.",
            is_active=True,
        )

        self.inactive_department = Department.objects.create(
            name="Inactive Department",
            is_active=False,
        )

        self.category = Category.objects.create(
            name="Road Repair",
            department=self.department,
            is_active=True,
        )

        self.inactive_category = Category.objects.create(
            name="Old Category",
            department=self.department,
            is_active=False,
        )

        self.user = User.objects.create_user(
            email="citizen@test.com",
            password="testpassword",
            role=User.Role.USER,
        )

        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="testpassword",
            role=User.Role.ADMIN,
        )

        self.officer = User.objects.create_user(
            email="officer@test.com",
            password="testpassword",
            role=User.Role.OFFICER,
            department=self.department,
        )

    def test_categories_require_authentication(self):
        response = self.client.get(
            reverse("active-category-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_authenticated_user_can_list_active_categories(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            reverse("active-category-list")
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
            self.category.id,
            returned_ids,
        )

        self.assertNotIn(
            self.inactive_category.id,
            returned_ids,
        )

    def test_authenticated_user_can_list_active_departments(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            reverse("active-department-list")
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
            self.department.id,
            returned_ids,
        )

        self.assertNotIn(
            self.inactive_department.id,
            returned_ids,
        )

    def test_officer_list_is_admin_only(self):
        self.client.force_authenticate(
            user=self.officer
        )

        response = self.client.get(
            reverse("active-officer-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_citizen_cannot_access_officer_list(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            reverse("active-officer-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_can_list_active_officers(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            reverse("active-officer-list")
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
            self.officer.id,
            returned_ids,
        )

    def test_admin_can_filter_officers_by_department(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.get(
            reverse("active-officer-list"),
            {
                "department": self.department.id,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        for officer in response.data:
            self.assertEqual(
                officer["department_id"],
                self.department.id,
            )