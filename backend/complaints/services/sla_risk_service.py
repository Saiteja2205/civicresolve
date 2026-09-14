from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from complaints.models import (
    Complaint,
    ComplaintHistory,
    ComplaintSLA,
)


class SLARiskError(Exception):
    """
    Raised when predictive SLA risk cannot be calculated safely.
    """

    pass


TERMINAL_STATUSES = {
    Complaint.Status.RESOLVED,
    Complaint.Status.CLOSED,
    Complaint.Status.REJECTED,
}


PRIORITY_WEIGHTS = {
    Complaint.Priority.LOW: 0,
    Complaint.Priority.MEDIUM: 5,
    Complaint.Priority.HIGH: 10,
    Complaint.Priority.CRITICAL: 15,
}


STATUS_WEIGHTS = {
    Complaint.Status.SUBMITTED: 20,
    Complaint.Status.AI_ANALYZING: 15,
    Complaint.Status.ASSIGNED: 10,
    Complaint.Status.ACKNOWLEDGED: 10,
    Complaint.Status.IN_PROGRESS: 5,
    Complaint.Status.REOPENED: 20,
    Complaint.Status.ESCALATED: 30,
}


def _clamp(value, minimum=0, maximum=100):
    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def _risk_level(score):
    if score >= 75:
        return "CRITICAL"

    if score >= 55:
        return "HIGH"

    if score >= 30:
        return "MEDIUM"

    return "LOW"


def _hours_between(start, end):
    if not start or not end:
        return 0.0

    seconds = (
        end - start
    ).total_seconds()

    return max(
        0.0,
        seconds / 3600,
    )


def _progress_ratio(
    start_time,
    deadline,
    now,
):
    total_seconds = (
        deadline - start_time
    ).total_seconds()

    if total_seconds <= 0:
        return 1.0

    elapsed_seconds = (
        now - start_time
    ).total_seconds()

    return max(
        0.0,
        elapsed_seconds / total_seconds,
    )


def _get_resolution_progress(
    complaint,
    sla,
    now,
):
    ratio = _progress_ratio(
        complaint.created_at,
        sla.resolution_deadline,
        now,
    )

    return _clamp(
        round(
            ratio * 100,
            2,
        ),
        0,
        100,
    )


def _get_response_progress(
    complaint,
    sla,
    now,
):
    ratio = _progress_ratio(
        complaint.created_at,
        sla.response_deadline,
        now,
    )

    return _clamp(
        round(
            ratio * 100,
            2,
        ),
        0,
        100,
    )


def _get_active_assignment(complaint):
    return (
        complaint.assignments
        .filter(
            unassigned_at__isnull=True,
        )
        .select_related(
            "officer",
            "department",
        )
        .order_by(
            "-assigned_at",
        )
        .first()
    )


def _get_officer_workload(assignment):
    if not assignment:
        return 0

    return Complaint.objects.filter(
        assignments__officer=assignment.officer,
        assignments__unassigned_at__isnull=True,
    ).exclude(
        status__in=TERMINAL_STATUSES,
    ).distinct().count()


def _get_department_breach_rate(complaint):
    if not complaint.category_id:
        return 0.0

    department_id = (
        complaint.category.department_id
    )

    completed_slas = (
        ComplaintSLA.objects
        .filter(
            complaint__category__department_id=department_id,
            resolution_completed_at__isnull=False,
        )
        .exclude(
            complaint_id=complaint.id,
        )
    )

    total = completed_slas.count()

    if total == 0:
        return 0.0

    breached = completed_slas.filter(
        resolution_breached=True,
    ).count()

    return round(
        (breached / total) * 100,
        2,
    )


def _get_last_activity(complaint):
    return (
        ComplaintHistory.objects
        .filter(
            complaint=complaint,
        )
        .order_by(
            "-created_at",
        )
        .first()
    )


def _get_urgency_score(complaint):
    try:
        analysis = complaint.analysis
    except Exception:
        return 0

    if analysis.urgency_score is None:
        return 0

    return float(
        analysis.urgency_score
    )


def calculate_sla_risk(complaint):
    """
    Calculate an explainable predictive SLA risk score.

    The score combines:
    - SLA deadline progress
    - response deadline pressure
    - complaint priority
    - AI urgency
    - complaint status
    - inactivity
    - officer workload
    - historical department breach rate

    This is intentionally explainable and deterministic.
    It does not claim to be a calibrated probability.
    """

    try:
        sla = complaint.sla
    except ComplaintSLA.DoesNotExist as exc:
        raise SLARiskError(
            "Complaint does not have an SLA."
        ) from exc

    now = timezone.now()

    if complaint.status in TERMINAL_STATUSES:
        return {
            "complaint": complaint.id,
            "ticket_number": complaint.ticket_number,
            "risk_score": 0,
            "risk_level": "LOW",
            "risk_label": "No active SLA risk",
            "prediction_basis": (
                "Complaint is in a terminal state."
            ),
            "as_of": now,
            "resolution_progress_percent": 100.0,
            "response_progress_percent": 100.0,
            "resolution_hours_remaining": 0.0,
            "response_hours_remaining": 0.0,
            "response_breached": (
                sla.response_breached
            ),
            "resolution_breached": (
                sla.resolution_breached
            ),
            "officer_workload": 0,
            "department_breach_rate_percent": 0.0,
            "urgency_score": 0.0,
            "factors": [],
            "recommended_action": (
                "No active SLA intervention is required."
            ),
        }

    score = 0
    factors = []

    resolution_progress = (
        _get_resolution_progress(
            complaint,
            sla,
            now,
        )
    )

    response_progress = (
        _get_response_progress(
            complaint,
            sla,
            now,
        )
    )

    resolution_hours_remaining = max(
        0.0,
        _hours_between(
            now,
            sla.resolution_deadline,
        ),
    )

    response_hours_remaining = max(
        0.0,
        _hours_between(
            now,
            sla.response_deadline,
        ),
    )

    # Resolution deadline pressure.
    if sla.resolution_breached:
        score += 70

        factors.append(
            "Resolution SLA has already been breached."
        )

    elif resolution_progress >= 90:
        score += 55

        factors.append(
            "More than 90% of the resolution SLA has elapsed."
        )

    elif resolution_progress >= 75:
        score += 40

        factors.append(
            "More than 75% of the resolution SLA has elapsed."
        )

    elif resolution_progress >= 50:
        score += 25

        factors.append(
            "More than half of the resolution SLA has elapsed."
        )

    elif resolution_progress >= 25:
        score += 10

        factors.append(
            "The complaint has entered the active SLA window."
        )

    # Response deadline pressure.
    if sla.response_breached:
        score += 20

        factors.append(
            "Response SLA has already been breached."
        )

    elif response_progress >= 75:
        score += 10

        factors.append(
            "Response deadline is approaching."
        )

    # Complaint priority.
    priority_weight = PRIORITY_WEIGHTS.get(
        complaint.priority,
        0,
    )

    if priority_weight > 0:
        score += priority_weight

        factors.append(
            f"Complaint priority is {complaint.priority}."
        )

    # AI urgency.
    urgency_score = _get_urgency_score(
        complaint
    )

    if urgency_score >= 80:
        score += 10

        factors.append(
            "AI urgency assessment is very high."
        )

    elif urgency_score >= 60:
        score += 7

        factors.append(
            "AI urgency assessment is high."
        )

    elif urgency_score >= 40:
        score += 4

        factors.append(
            "AI urgency assessment is moderate."
        )

    # Current status.
    status_weight = STATUS_WEIGHTS.get(
        complaint.status,
        0,
    )

    if status_weight > 0:
        score += status_weight

        if complaint.status in {
            Complaint.Status.REOPENED,
            Complaint.Status.ESCALATED,
        }:
            factors.append(
                f"Complaint status is {complaint.status}."
            )

    # Last activity / inactivity.
    last_activity = _get_last_activity(
        complaint
    )

    inactivity_hours = (
        _hours_between(
            last_activity.created_at
            if last_activity
            else complaint.created_at,
            now,
        )
    )

    if inactivity_hours >= 24:
        score += 15

        factors.append(
            "No complaint activity has been recorded for at least 24 hours."
        )

    elif inactivity_hours >= 12:
        score += 10

        factors.append(
            "Complaint activity has been inactive for at least 12 hours."
        )

    elif inactivity_hours >= 6:
        score += 5

        factors.append(
            "Complaint activity has been inactive for at least 6 hours."
        )

    # Officer workload.
    assignment = _get_active_assignment(
        complaint
    )

    officer_workload = _get_officer_workload(
        assignment
    )

    if officer_workload >= 8:
        score += 15

        factors.append(
            "Assigned officer has a high active workload."
        )

    elif officer_workload >= 5:
        score += 10

        factors.append(
            "Assigned officer has an elevated active workload."
        )

    elif officer_workload >= 3:
        score += 5

        factors.append(
            "Assigned officer has multiple active complaints."
        )

    # Historical department performance.
    department_breach_rate = (
        _get_department_breach_rate(
            complaint
        )
    )

    if department_breach_rate >= 50:
        score += 10

        factors.append(
            "The responsible department has a high historical SLA breach rate."
        )

    elif department_breach_rate >= 25:
        score += 5

        factors.append(
            "The responsible department has a notable historical SLA breach rate."
        )

    score = _clamp(
        round(score)
    )

    risk_level = _risk_level(
        score
    )

    if risk_level == "CRITICAL":
        recommended_action = (
            "Immediate administrator/officer intervention is recommended."
        )

    elif risk_level == "HIGH":
        recommended_action = (
            "Prioritize this complaint and review the assigned officer workload."
        )

    elif risk_level == "MEDIUM":
        recommended_action = (
            "Monitor the complaint closely and act before the SLA window narrows."
        )

    else:
        recommended_action = (
            "Continue normal monitoring."
        )

    if not factors:
        factors.append(
            "No significant SLA risk signals detected."
        )

    return {
        "complaint": complaint.id,
        "ticket_number": complaint.ticket_number,
        "risk_score": score,
        "risk_level": risk_level,
        "risk_label": (
            f"{risk_level.title()} SLA breach risk"
        ),
        "prediction_basis": (
            "Explainable predictive scoring using SLA progress, "
            "priority, AI urgency, activity, workload, and historical "
            "department performance."
        ),
        "as_of": now,
        "resolution_progress_percent": (
            resolution_progress
        ),
        "response_progress_percent": (
            response_progress
        ),
        "resolution_hours_remaining": round(
            resolution_hours_remaining,
            2,
        ),
        "response_hours_remaining": round(
            response_hours_remaining,
            2,
        ),
        "response_breached": (
            sla.response_breached
        ),
        "resolution_breached": (
            sla.resolution_breached
        ),
        "officer_workload": (
            officer_workload
        ),
        "department_breach_rate_percent": (
            department_breach_rate
        ),
        "urgency_score": (
            round(
                urgency_score,
                2,
            )
        ),
        "factors": factors,
        "recommended_action": (
            recommended_action
        ),
    }