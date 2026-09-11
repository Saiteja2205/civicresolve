from django.db.models import Count, Q

from accounts.models import User
from complaints.models import ComplaintAssignment


class OfficerAssignmentError(Exception):
    """
    Raised when a suitable officer cannot be selected.
    """

    pass


def get_officer_workload(officer):
    """
    Return the number of currently active complaints
    assigned to an officer.
    """

    return ComplaintAssignment.objects.filter(
        officer=officer,
        unassigned_at__isnull=True,
    ).count()


def select_officer_for_department(department):
    """
    Select an active officer belonging to the specified
    department.

    Officers are ranked by their current active workload.
    The officer with the lowest workload is selected.

    User ID is used as a deterministic tie-breaker.
    """

    officers = (
        User.objects
        .filter(
            role=User.Role.OFFICER,
            department=department,
            is_active=True,
        )
        .annotate(
            active_complaint_count=Count(
                "complaint_assignments",
                filter=Q(
                    complaint_assignments__unassigned_at__isnull=True
                ),
            )
        )
        .order_by(
            "active_complaint_count",
            "id",
        )
    )

    officer = officers.first()

    if officer is None:
        raise OfficerAssignmentError(
            f"No active officer is available for "
            f"department '{department.name}'."
        )

    return officer