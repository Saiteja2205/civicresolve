from django.db import transaction

from complaints.models import Complaint, ComplaintAnalysis
from complaints.services.ai_output_validator import validate_ai_output


@transaction.atomic
def create_ai_analysis(complaint, ai_output=None):
    """
    Create or update the AI analysis for a complaint.

    ai_output is expected to be a dictionary containing
    structured AI results.

    The actual AI provider will be connected later.
    """

    if ai_output is None:
        ai_output = {
            "summary": (
                "AI analysis has not been generated yet."
            ),
            "predicted_category": None,
            "predicted_department": None,
            "predicted_priority": complaint.priority,
            "urgency_score": 50,
            "confidence_score": 0,
        }

    validated_output = validate_ai_output(ai_output)

    analysis, created = ComplaintAnalysis.objects.update_or_create(
        complaint=complaint,
        defaults={
            "summary": validated_output["summary"],
            "predicted_category_id": (
                validated_output["predicted_category"]
            ),
            "predicted_department_id": (
                validated_output["predicted_department"]
            ),
            "predicted_priority": (
                validated_output["predicted_priority"]
            ),
            "urgency_score": (
                validated_output["urgency_score"]
            ),
            "confidence_score": (
                validated_output["confidence_score"]
            ),
            "model_name": "CivicResolve-AI-Placeholder-v1",
        },
    )

    return analysis