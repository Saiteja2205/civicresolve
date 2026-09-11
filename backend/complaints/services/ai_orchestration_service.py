from complaints.models import Complaint
from complaints.services.ai_analysis_service import (
    create_ai_analysis,
)
from complaints.services.complaint_service import (
    change_complaint_status,
)
from complaints.services.ai_provider import AIProviderError


def run_ai_analysis(complaint):
    """
    Run AI analysis for a complaint.

    The complaint is moved to AI_ANALYZING while
    the analysis is being generated.

    If AI succeeds, the analysis is saved and the
    complaint is moved back to SUBMITTED.

    If AI fails, the complaint remains submitted
    and the error is returned to the caller.
    """

    change_complaint_status(
        complaint=complaint,
        new_status=Complaint.Status.AI_ANALYZING,
        comment="AI complaint analysis started.",
    )

    try:
        analysis = create_ai_analysis(
            complaint=complaint
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

    change_complaint_status(
        complaint=complaint,
        new_status=Complaint.Status.SUBMITTED,
        comment="AI complaint analysis completed.",
    )

    return {
        "success": True,
        "analysis": analysis,
        "error": None,
    }