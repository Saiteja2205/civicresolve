from datetime import timedelta

from django.db import transaction

from complaints.models import Complaint, ComplaintSLA, SLAPolicy


class SLAError(Exception):
    """
    Raised when an SLA cannot be created safely.
    """
    pass


def get_sla_policy_for_priority(priority):
    """
    Return the active SLA policy for a complaint priority.
    """

    try:
        return SLAPolicy.objects.get(
            priority=priority,
            is_active=True,
        )
    except SLAPolicy.DoesNotExist as exc:
        raise SLAError(
            f"No active SLA policy exists for priority '{priority}'."
        ) from exc


@transaction.atomic
def create_complaint_sla(complaint):
    """
    Create or update the SLA for a complaint based on its priority.

    Response and resolution deadlines are calculated from the
    complaint creation time.
    """

    policy = get_sla_policy_for_priority(
        complaint.priority
    )

    start_time = complaint.created_at

    response_deadline = (
        start_time
        + timedelta(hours=policy.response_time_hours)
    )

    resolution_deadline = (
        start_time
        + timedelta(hours=policy.resolution_time_hours)
    )

    sla, created = ComplaintSLA.objects.update_or_create(
        complaint=complaint,
        defaults={
            "policy": policy,
            "response_deadline": response_deadline,
            "resolution_deadline": resolution_deadline,
        },
    )

    return sla