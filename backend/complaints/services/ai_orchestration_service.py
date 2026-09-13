from django.db import transaction

from complaints.models import Complaint
from complaints.services.ai_analysis_service import (
    create_ai_analysis,
)
from complaints.services.ai_provider import (
    AIProviderError,
)
from complaints.services.complaint_service import (
    change_complaint_status,
)


@transaction.atomic
def run_ai_analysis(complaint):
    """
    Run AI analysis for a complaint.

    The complaint is moved to AI_ANALYZING while the analysis
    is being generated.

    If AI succeeds, the analysis is saved and the complaint
    remains in AI_ANALYZING so that automatic routing and
    assignment can continue.

    If AI fails, the complaint is returned to SUBMITTED and
    the failure is recorded through the status history.

    The complete operation is transactional so that a failure
    during the recovery transition cannot leave a partially
    updated AI-analysis workflow.
    """

    change_complaint_status(
        complaint=complaint,
        new_status=Complaint.Status.AI_ANALYZING,
        comment="AI complaint analysis started.",
    )

    try:
        analysis = create_ai_analysis(
            complaint=complaint,
        )

    except AIProviderError as exc:
        change_complaint_status(
            complaint=complaint,
            new_status=Complaint.Status.SUBMITTED,
            comment=(
                "AI analysis could not be completed. "
                "Complaint remains submitted."
            ),
        )

        return {
            "success": False,
            "analysis": None,
            "error": str(exc),
        }

    return {
        "success": True,
        "analysis": analysis,
        "error": None,
    }