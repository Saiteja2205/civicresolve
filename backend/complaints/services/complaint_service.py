from django.db import transaction
from django.utils import timezone

from complaints.models import (
    Complaint,
    ComplaintHistory,
)
from notifications.models import Notification
from notifications.services import (
    create_notification,
    notify_assigned_officer,
    notify_complaint_user,
)


VALID_TRANSITIONS = {
    Complaint.Status.SUBMITTED: {
        Complaint.Status.AI_ANALYZING,
        Complaint.Status.ASSIGNED,
        Complaint.Status.REJECTED,
    },

    Complaint.Status.AI_ANALYZING: {
        Complaint.Status.ASSIGNED,
        Complaint.Status.SUBMITTED,
    },

    Complaint.Status.ASSIGNED: {
        Complaint.Status.ACKNOWLEDGED,
    },

    Complaint.Status.ACKNOWLEDGED: {
        Complaint.Status.IN_PROGRESS,
    },

    Complaint.Status.IN_PROGRESS: {
        Complaint.Status.RESOLVED,
        Complaint.Status.NEEDS_INFORMATION,
        Complaint.Status.ESCALATED,
    },

    Complaint.Status.NEEDS_INFORMATION: {
        Complaint.Status.IN_PROGRESS,
    },

    Complaint.Status.ESCALATED: {
        Complaint.Status.IN_PROGRESS,
        Complaint.Status.RESOLVED,
    },

    Complaint.Status.RESOLVED: {
        Complaint.Status.CLOSED,
        Complaint.Status.REOPENED,
    },

    Complaint.Status.REOPENED: {
        Complaint.Status.ASSIGNED,
    },

    Complaint.Status.CLOSED: set(),

    Complaint.Status.REJECTED: set(),
}


STATUS_LABELS = {
    Complaint.Status.SUBMITTED: "Submitted",
    Complaint.Status.AI_ANALYZING: "AI analysis",
    Complaint.Status.ASSIGNED: "Assigned",
    Complaint.Status.ACKNOWLEDGED: "Acknowledged",
    Complaint.Status.IN_PROGRESS: "In progress",
    Complaint.Status.NEEDS_INFORMATION: (
        "Needs information"
    ),
    Complaint.Status.ESCALATED: "Escalated",
    Complaint.Status.RESOLVED: "Resolved",
    Complaint.Status.CLOSED: "Closed",
    Complaint.Status.REOPENED: "Reopened",
    Complaint.Status.REJECTED: "Rejected",
}


def get_status_label(status):
    return STATUS_LABELS.get(
        status,
        status.replace("_", " ").title(),
    )


@transaction.atomic
def change_complaint_status(
    complaint,
    new_status,
    changed_by=None,
    comment="",
):
    old_status = complaint.status

    allowed_statuses = VALID_TRANSITIONS.get(
        old_status,
        set(),
    )

    if new_status not in allowed_statuses:
        raise ValueError(
            f"Invalid status transition: "
            f"{old_status} → {new_status}"
        )

    complaint.status = new_status

    if new_status == Complaint.Status.RESOLVED:
        complaint.resolved_at = timezone.now()

    if new_status == Complaint.Status.CLOSED:
        complaint.closed_at = timezone.now()

    complaint.save()

    ComplaintHistory.objects.create(
        complaint=complaint,
        changed_by=changed_by,
        old_status=old_status,
        new_status=new_status,
        comment=comment,
    )

    old_label = get_status_label(old_status)
    new_label = get_status_label(new_status)

    notify_complaint_user(
        complaint=complaint,
        notification_type=(
            Notification.NotificationType
            .STATUS_CHANGED
        ),
        title="Complaint status updated",
        message=(
            f"Your complaint "
            f"{complaint.ticket_number} "
            f"changed from {old_label} "
            f"to {new_label}."
        ),
        metadata={
            "event": "status_changed",
            "old_status": old_status,
            "new_status": new_status,
        },
    )

    notify_assigned_officer(
        complaint=complaint,
        notification_type=(
            Notification.NotificationType
            .STATUS_CHANGED
        ),
        title="Complaint status updated",
        message=(
            f"Complaint "
            f"{complaint.ticket_number} "
            f"changed from {old_label} "
            f"to {new_label}."
        ),
        metadata={
            "event": "status_changed",
            "old_status": old_status,
            "new_status": new_status,
        },
    )

    return complaint