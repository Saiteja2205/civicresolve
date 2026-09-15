from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from notifications.models import Notification
from notifications.services import (
    create_notification,
    mark_all_notifications_read,
    mark_notification_read,
)


class NotificationServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="notification-user@test.local",
            password="TestPassword123!",
            role=User.Role.USER,
            is_active=True,
        )

    def test_create_notification(self):
        notification = create_notification(
            recipient=self.user,
            notification_type=(
                Notification.NotificationType.SYSTEM
            ),
            title="Test notification",
            message="This is a test.",
        )

        self.assertEqual(
            Notification.objects.count(),
            1,
        )

        self.assertEqual(
            notification.recipient,
            self.user,
        )

        self.assertFalse(
            notification.is_read,
        )

    def test_mark_notification_read(self):
        notification = create_notification(
            recipient=self.user,
            notification_type=(
                Notification.NotificationType.SYSTEM
            ),
            title="Test notification",
            message="This is a test.",
        )

        mark_notification_read(
            notification=notification,
        )

        notification.refresh_from_db()

        self.assertTrue(
            notification.is_read,
        )

        self.assertIsNotNone(
            notification.read_at,
        )

    def test_mark_all_notifications_read(self):
        for index in range(3):
            create_notification(
                recipient=self.user,
                notification_type=(
                    Notification.NotificationType.SYSTEM
                ),
                title=f"Test {index}",
                message="Test notification.",
            )

        updated_count = (
            mark_all_notifications_read(
                recipient=self.user,
            )
        )

        self.assertEqual(
            updated_count,
            3,
        )

        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user,
                is_read=False,
            ).count(),
            0,
        )


class NotificationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="api-user@test.local",
            password="TestPassword123!",
            role=User.Role.USER,
            is_active=True,
        )

        self.other_user = User.objects.create_user(
            email="other-user@test.local",
            password="TestPassword123!",
            role=User.Role.USER,
            is_active=True,
        )

    def test_unauthenticated_list_is_rejected(self):
        response = self.client.get(
            reverse("notification-list"),
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_authenticated_user_can_list_notifications(
        self,
    ):
        create_notification(
            recipient=self.user,
            notification_type=(
                Notification.NotificationType.SYSTEM
            ),
            title="Hello",
            message="Hello notification.",
        )

        create_notification(
            recipient=self.other_user,
            notification_type=(
                Notification.NotificationType.SYSTEM
            ),
            title="Private",
            message="Other user's notification.",
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            reverse("notification-list"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data["notifications"]),
            1,
        )

        self.assertEqual(
            response.data["unread_count"],
            1,
        )

        self.assertEqual(
            response.data["notifications"][0]["title"],
            "Hello",
        )

    def test_user_can_mark_own_notification_read(
        self,
    ):
        notification = create_notification(
            recipient=self.user,
            notification_type=(
                Notification.NotificationType.SYSTEM
            ),
            title="Read me",
            message="Read notification.",
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            reverse(
                "notification-read",
                kwargs={
                    "notification_id": notification.id,
                },
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        notification.refresh_from_db()

        self.assertTrue(
            notification.is_read,
        )

    def test_user_cannot_mark_other_users_notification_read(
        self,
    ):
        notification = create_notification(
            recipient=self.other_user,
            notification_type=(
                Notification.NotificationType.SYSTEM
            ),
            title="Private",
            message="Private notification.",
        )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            reverse(
                "notification-read",
                kwargs={
                    "notification_id": notification.id,
                },
            ),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        notification.refresh_from_db()

        self.assertFalse(
            notification.is_read,
        )

    def test_user_can_mark_all_notifications_read(
        self,
    ):
        for index in range(2):
            create_notification(
                recipient=self.user,
                notification_type=(
                    Notification.NotificationType.SYSTEM
                ),
                title=f"Notification {index}",
                message="Test.",
            )

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            reverse("notification-read-all"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["updated_count"],
            2,
        )

        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user,
                is_read=False,
            ).count(),
            0,
        )