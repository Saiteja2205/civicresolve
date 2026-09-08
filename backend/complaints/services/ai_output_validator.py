from decimal import Decimal, InvalidOperation

from complaints.models import Complaint


VALID_PRIORITIES = {
    Complaint.Priority.LOW,
    Complaint.Priority.MEDIUM,
    Complaint.Priority.HIGH,
    Complaint.Priority.CRITICAL,
}


def validate_ai_output(data):
    """
    Validate structured output returned by the AI system.

    Returns:
        dict: Cleaned and validated AI output.

    Raises:
        ValueError: If the AI output is invalid.
    """

    if not isinstance(data, dict):
        raise ValueError("AI output must be a JSON object.")

    required_fields = [
        "summary",
        "predicted_priority",
        "urgency_score",
        "confidence_score",
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(
                f"AI output is missing required field: {field}"
            )

    summary = data["summary"]

    if not isinstance(summary, str):
        raise ValueError("AI summary must be a string.")

    summary = summary.strip()

    if not summary:
        raise ValueError("AI summary cannot be empty.")

    if len(summary) > 2000:
        raise ValueError(
            "AI summary cannot exceed 2000 characters."
        )

    predicted_priority = data["predicted_priority"]

    if predicted_priority not in VALID_PRIORITIES:
        raise ValueError(
            "AI returned an invalid priority."
        )

    try:
        urgency_score = Decimal(
            str(data["urgency_score"])
        )
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(
            "Urgency score must be a valid number."
        )

    try:
        confidence_score = Decimal(
            str(data["confidence_score"])
        )
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(
            "Confidence score must be a valid number."
        )

    if urgency_score < 0 or urgency_score > 100:
        raise ValueError(
            "Urgency score must be between 0 and 100."
        )

    if confidence_score < 0 or confidence_score > 100:
        raise ValueError(
            "Confidence score must be between 0 and 100."
        )

    return {
        "summary": summary,
        "predicted_category": data.get(
            "predicted_category"
        ),
        "predicted_department": data.get(
            "predicted_department"
        ),
        "predicted_priority": predicted_priority,
        "urgency_score": urgency_score,
        "confidence_score": confidence_score,
    }