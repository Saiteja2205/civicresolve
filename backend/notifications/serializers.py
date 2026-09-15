from rest_framework import serializers

from notifications.models import Notification


class NotificationSerializer(
    serializers.ModelSerializer,
):
    complaint_ticket = serializers.CharField(
        source="complaint.ticket_number",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "complaint",
            "complaint_ticket",
            "metadata",
            "is_read",
            "created_at",
            "read_at",
        ]
        read_only_fields = fields