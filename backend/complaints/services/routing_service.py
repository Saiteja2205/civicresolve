from complaints.models import Complaint, ComplaintAnalysis
from organizations.models import Category, Department


class RoutingError(Exception):
    """
    Raised when a complaint cannot be routed safely.
    """

    pass


def route_complaint(complaint):
    """
    Determine the department responsible for a complaint
    using its validated AI category.

    The department is derived from the category stored
    in ComplaintAnalysis rather than trusting an AI-supplied
    department independently.
    """

    try:
        analysis = complaint.analysis
    except ComplaintAnalysis.DoesNotExist as exc:
        raise RoutingError(
            "Complaint does not have an AI analysis."
        ) from exc

    if not analysis.predicted_category_id:
        raise RoutingError(
            "AI analysis does not contain a predicted category."
        )

    category = (
        Category.objects
        .filter(
            id=analysis.predicted_category_id,
            is_active=True,
            department__is_active=True,
        )
        .select_related("department")
        .first()
    )

    if category is None:
        raise RoutingError(
            "Predicted category is invalid or inactive."
        )

    department = category.department

    if not department.is_active:
        raise RoutingError(
            "The category's department is inactive."
        )

    if (
        analysis.predicted_department_id
        and analysis.predicted_department_id
        != department.id
    ):
        raise RoutingError(
            "AI department does not match the category's "
            "actual department."
        )

    return {
        "category": category,
        "department": department,
    }