from django.db import transaction
from django.utils import timezone

from complaints.models import Complaint, ComplaintHistory, ComplaintSLA


class SLAMonitoringError(Exception):
    """
    Raised when SLA monitoring cannot be completed safely.
    """
    pass


@transaction.atomic
def check_complaint_sla(complaint):
    """
    Check whether the complaint has breached its response
    or resolution SLA.

    Response and resolution breaches are stored on ComplaintSLA.

    If the resolution SLA has been breached, the complaint is
    escalated unless it is already in a terminal state.
    """

    try:
        sla = complaint.sla
    except ComplaintSLA.DoesNotExist as exc:
        raise SLAMonitoringError(
            "Complaint does not have an SLA."
        ) from exc

    now = timezone.now()

    response_breached = (
        now > sla.response_deadline
        and sla.response_completed_at is None
    )

    resolution_breached = (
        now > sla.resolution_deadline
        and sla.resolution_completed_at is None
    )

    sla.response_breached = (
        sla.response_breached or response_breached
    )

    sla.resolution_breached = (
        sla.resolution_breached or resolution_breached
    )

    sla.save(
        update_fields=[
            "response_breached",
            "resolution_breached",
            "updated_at",
        ]
    )

    escalated = False

    if (
        resolution_breached
        and complaint.status
        not in {
            Complaint.Status.RESOLVED,
            Complaint.Status.CLOSED,
            Complaint.Status.REJECTED,
            Complaint.Status.ESCALATED,
        }
    ):
        old_status = complaint.status

        complaint.status = Complaint.Status.ESCALATED
        complaint.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        ComplaintHistory.objects.create(
            complaint=complaint,
            changed_by=None,
            old_status=old_status,
            new_status=Complaint.Status.ESCALATED,
            comment=(
                "Complaint automatically escalated because "
                "the resolution SLA was breached."
            ),
        )

        escalated = True

    return {
        "complaint": complaint,
        "sla": sla,
        "response_breached": sla.response_breached,
        "resolution_breached": sla.resolution_breached,
        "escalated": escalated,
    }