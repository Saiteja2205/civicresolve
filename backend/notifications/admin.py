from django.contrib import admin

from notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "recipient",
        "notification_type",
        "title",
        "is_read",
        "created_at",
        "read_at",
    )

    list_filter = (
        "notification_type",
        "is_read",
        "created_at",
    )

    search_fields = (
        "recipient__email",
        "title",
        "message",
        "complaint__ticket_number",
    )

    readonly_fields = (
        "created_at",
        "read_at",
    )