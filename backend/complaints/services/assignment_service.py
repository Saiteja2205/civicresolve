from django.db import transaction

from accounts.models import User
from complaints.models import Complaint, ComplaintAssignment
from complaints.services.complaint_service import change_complaint_status
from complaints.services.officer_assignment_service import (
    OfficerAssignmentError,
    select_officer_for_department,
)
from complaints.services.routing_service import (
    RoutingError,
    route_complaint,
)


class ComplaintAssignmentError(Exception):
    """
    Raised when a complaint cannot be assigned safely.
    """
    pass


def get_system_assignment_user():
    """
    Return the system user responsible for automatic assignments.
    """
    try:
        return User.objects.get(
            email="system@civicresolve.local",
            role=User.Role.ADMIN,
            is_active=True,
        )
    except User.DoesNotExist as exc:
        raise ComplaintAssignmentError(
            "System assignment user does not exist or is inactive."
        ) from exc


@transaction.atomic
def assign_complaint(complaint):
    """
    Automatically assign a complaint to the least-loaded
    active officer in the department responsible for the
    complaint's validated AI category.

    The operation creates a ComplaintAssignment record,
    changes the complaint status to ASSIGNED, and records
    the status change in ComplaintHistory.
    """

    if complaint.status != Complaint.Status.AI_ANALYZING:
        raise ComplaintAssignmentError(
            f"Complaint must be in AI_ANALYZING status before "
            f"automatic assignment. Current status: "
            f"{complaint.status}"
        )

    existing_assignment = (
        ComplaintAssignment.objects
        .filter(
            complaint=complaint,
            unassigned_at__isnull=True,
        )
        .first()
    )

    if existing_assignment is not None:
        raise ComplaintAssignmentError(
            "Complaint already has an active assignment."
        )

    try:
        routing = route_complaint(complaint)
    except RoutingError as exc:
        raise ComplaintAssignmentError(
            f"Complaint routing failed: {exc}"
        ) from exc

    department = routing["department"]

    try:
        officer = select_officer_for_department(department)
    except OfficerAssignmentError as exc:
        raise ComplaintAssignmentError(
            f"Officer selection failed: {exc}"
        ) from exc

    system_user = get_system_assignment_user()

    assignment = ComplaintAssignment.objects.create(
        complaint=complaint,
        department=department,
        officer=officer,
        assigned_by=system_user,
        reason="Automatically assigned based on AI routing and officer workload.",
    )

    change_complaint_status(
        complaint,
        Complaint.Status.ASSIGNED,
        changed_by=system_user,
        comment=(
            f"Automatically assigned to {officer.email} "
            f"in {department.name}."
        ),
    )

    return assignment