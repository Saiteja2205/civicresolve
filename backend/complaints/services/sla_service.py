from datetime import timedelta

from django.utils import timezone

from complaints.models import ComplaintSLA, SLAPolicy


def create_sla_for_complaint(complaint):
    policy = SLAPolicy.objects.filter(
        priority=complaint.priority,
        is_active=True,
    ).first()

    if not policy:
        raise ValueError(
            f"No active SLA policy found for priority "
            f"{complaint.priority}"
        )

    now = timezone.now()

    return ComplaintSLA.objects.create(
        complaint=complaint,
        policy=policy,
        response_deadline=(
            now + timedelta(hours=policy.response_time_hours)
        ),
        resolution_deadline=(
            now + timedelta(hours=policy.resolution_time_hours)
        ),
    )