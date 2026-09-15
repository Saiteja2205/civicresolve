from django.conf import settings
from django.db import models


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        COMPLAINT_SUBMITTED = (
            "COMPLAINT_SUBMITTED",
            "Complaint submitted",
        )
        COMPLAINT_ASSIGNED = (
            "COMPLAINT_ASSIGNED",
            "Complaint assigned",
        )
        STATUS_CHANGED = (
            "STATUS_CHANGED",
            "Status changed",
        )
        SLA_WARNING = (
            "SLA_WARNING",
            "SLA warning",
        )
        SLA_BREACH = (
            "SLA_BREACH",
            "SLA breach",
        )
        ESCALATED = (
            "ESCALATED",
            "Complaint escalated",
        )
        EVIDENCE_UPLOADED = (
            "EVIDENCE_UPLOADED",
            "Evidence uploaded",
        )
        SYSTEM = (
            "SYSTEM",
            "System notification",
        )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    notification_type = models.CharField(
        max_length=40,
        choices=NotificationType.choices,
    )

    title = models.CharField(
        max_length=200,
    )

    message = models.TextField()

    complaint = models.ForeignKey(
        "complaints.Complaint",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    is_read = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["recipient", "is_read"],
            ),
            models.Index(
                fields=["recipient", "created_at"],
            ),
        ]

    def __str__(self):
        return (
            f"{self.recipient.email} - "
            f"{self.title}"
        )