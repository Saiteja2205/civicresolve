from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from notifications.services import (
    mark_all_notifications_read,
    mark_notification_read,
)


class NotificationListView(APIView):
    """
    Return the authenticated user's latest notifications.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = (
            Notification.objects
            .filter(recipient=request.user)
            .select_related("complaint")
            .order_by("-created_at")[:50]
        )

        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()

        return Response(
            {
                "notifications": NotificationSerializer(
                    notifications,
                    many=True,
                ).data,
                "unread_count": unread_count,
            },
            status=status.HTTP_200_OK,
        )


class NotificationReadView(APIView):
    """
    Mark one notification as read.

    A user can only modify their own notification.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            recipient=request.user,
        )

        mark_notification_read(
            notification=notification,
        )

        return Response(
            NotificationSerializer(
                notification,
            ).data,
            status=status.HTTP_200_OK,
        )


class NotificationReadAllView(APIView):
    """
    Mark all notifications belonging to the
    authenticated user as read.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated_count = mark_all_notifications_read(
            recipient=request.user,
        )

        return Response(
            {
                "updated_count": updated_count,
            },
            status=status.HTTP_200_OK,
        )