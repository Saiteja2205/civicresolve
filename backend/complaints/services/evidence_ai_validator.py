from decimal import Decimal, InvalidOperation

from complaints.models import ComplaintEvidence


class EvidenceAIValidationError(Exception):
    """
    Raised when AI-generated evidence analysis is invalid.
    """

    pass


ALLOWED_EVIDENCE_TYPES = {
    choice[0]
    for choice in ComplaintEvidence.EvidenceType.choices
}


def _validate_score(value, field_name):
    """
    Validate a score between 0 and 100.
    """
    try:
        score = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise EvidenceAIValidationError(
            f"{field_name} must be a number."
        ) from exc

    if score < 0 or score > 100:
        raise EvidenceAIValidationError(
            f"{field_name} must be between 0 and 100."
        )

    return score


def validate_evidence_ai_output(data):
    """
    Validate structured AI output for complaint evidence.
    """
    if not isinstance(data, dict):
        raise EvidenceAIValidationError(
            "AI evidence analysis must be a JSON object."
        )

    required_fields = {
        "evidence_type",
        "observations",
        "severity_score",
        "confidence_score",
        "complaint_consistency",
        "analysis_explanation",
    }

    missing_fields = required_fields - set(data.keys())

    if missing_fields:
        raise EvidenceAIValidationError(
            "Missing AI fields: "
            + ", ".join(sorted(missing_fields))
        )

    evidence_type = data["evidence_type"]

    if evidence_type not in ALLOWED_EVIDENCE_TYPES:
        raise EvidenceAIValidationError(
            f"Invalid evidence_type: {evidence_type}"
        )

    observations = data["observations"]

    if not isinstance(observations, str):
        raise EvidenceAIValidationError(
            "observations must be a string."
        )

    analysis_explanation = data["analysis_explanation"]

    if not isinstance(analysis_explanation, str):
        raise EvidenceAIValidationError(
            "analysis_explanation must be a string."
        )

    complaint_consistency = data["complaint_consistency"]

    if not isinstance(complaint_consistency, bool):
        raise EvidenceAIValidationError(
            "complaint_consistency must be true or false."
        )

    severity_score = _validate_score(
        data["severity_score"],
        "severity_score",
    )

    confidence_score = _validate_score(
        data["confidence_score"],
        "confidence_score",
    )

    return {
        "evidence_type": evidence_type,
        "observations": observations.strip(),
        "severity_score": severity_score,
        "confidence_score": confidence_score,
        "complaint_consistency": complaint_consistency,
        "analysis_explanation": analysis_explanation.strip(),
    }