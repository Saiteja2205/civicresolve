from django.db import transaction
from django.utils import timezone

from complaints.models import Complaint, ComplaintHistory

VALID_TRANSITIONS = {
    Complaint.Status.SUBMITTED: {
        Complaint.Status.ASSIGNED,
        Complaint.Status.REJECTED,
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

    return complaint