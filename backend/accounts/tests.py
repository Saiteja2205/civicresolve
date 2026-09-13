from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient


User = get_user_model()


class AuthenticationAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="citizen@test.com",
            password="testpassword",
            role=User.Role.USER,
            first_name="Test",
            last_name="Citizen",
        )

    def test_valid_login_returns_tokens(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "email": "citizen@test.com",
                "password": "testpassword",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "access",
            response.data,
        )

        self.assertIn(
            "refresh",
            response.data,
        )

    def test_invalid_password_is_rejected(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "email": "citizen@test.com",
                "password": "wrongpassword",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_unknown_user_is_rejected(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "email": "unknown@test.com",
                "password": "testpassword",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_current_user_requires_authentication(self):
        response = self.client.get(
            reverse("current-user")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_current_user_returns_authenticated_user(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            reverse("current-user")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["email"],
            self.user.email,
        )

        self.assertEqual(
            response.data["role"],
            User.Role.USER,
        )


class ProfileAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="profile@test.com",
            password="testpassword",
            role=User.Role.USER,
            first_name="Old",
            last_name="Name",
            phone="9876543210",
        )

    def test_profile_requires_authentication(self):
        response = self.client.get(
            reverse("user-profile")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_authenticated_user_can_get_profile(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            reverse("user-profile")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["email"],
            self.user.email,
        )

        self.assertEqual(
            response.data["first_name"],
            "Old",
        )

    def test_authenticated_user_can_update_profile(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.patch(
            reverse("user-profile"),
            {
                "first_name": "Updated",
                "last_name": "Citizen",
                "phone": "9123456789",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.first_name,
            "Updated",
        )

        self.assertEqual(
            self.user.last_name,
            "Citizen",
        )

        self.assertEqual(
            self.user.phone,
            "9123456789",
        )

    def test_profile_rejects_invalid_phone(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.patch(
            reverse("user-profile"),
            {
                "phone": "invalid-phone",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_email_is_not_changeable_through_profile(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.patch(
            reverse("user-profile"),
            {
                "email": "changed@test.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.email,
            "profile@test.com",
        )