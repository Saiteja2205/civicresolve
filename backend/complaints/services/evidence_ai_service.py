import json
from datetime import datetime, timezone

from complaints.models import ComplaintEvidence
from complaints.services.ai_provider import (
    AIProviderError,
    GeminiProvider,
)
from complaints.services.evidence_ai_validator import (
    EvidenceAIValidationError,
    validate_evidence_ai_output,
)


class EvidenceAIAnalysisError(Exception):
    """
    Raised when evidence AI analysis cannot be completed.
    """

    pass


def build_evidence_prompt(complaint, evidence):
    """
    Build a multimodal prompt for analyzing complaint evidence.

    The AI receives the citizen's complaint context together with
    the uploaded image and returns structured evidence metadata.
    """
    category_name = (
        complaint.category.name
        if complaint.category
        else "Not specified"
    )

    department_name = (
        complaint.category.department.name
        if complaint.category
        else "Not specified"
    )

    return f"""
You are the evidence-analysis component of CivicResolve,
an intelligent grievance management system.

Analyze the attached complaint evidence image together with
the citizen's complaint information.

Complaint ticket:
{complaint.ticket_number}

Complaint title:
{complaint.title}

Complaint description:
{complaint.description}

Citizen-selected category:
{category_name}

Responsible department:
{department_name}

Return ONLY valid JSON.

Required JSON structure:

{{
  "evidence_type": "ROAD_DAMAGE | WATER_LEAKAGE | GARBAGE | STREET_LIGHTING | ELECTRICITY | PUBLIC_SAFETY | SANITATION | OTHER",
  "observations": "A concise factual description of what is visibly present in the image.",
  "severity_score": 0,
  "confidence_score": 0,
  "complaint_consistency": true,
  "analysis_explanation": "A concise explanation of whether the visible evidence is consistent with the complaint."
}}

Rules:

1. Describe only visible evidence.
2. Do not invent objects, people, damage, locations, or events that
   cannot reasonably be determined from the image.
3. severity_score must be an integer from 0 to 100.
4. confidence_score must be an integer from 0 to 100.
5. complaint_consistency must be true only when the visible image
   reasonably supports the complaint.
6. Use OTHER when the evidence does not clearly fit one of the
   supported evidence types.
7. Keep observations concise.
8. Keep analysis_explanation concise.
9. Do not include markdown.
10. Do not include additional JSON fields.
"""


def analyze_evidence(evidence):
    """
    Analyze a ComplaintEvidence image using Gemini Vision.

    The original evidence remains stored even if AI analysis fails.
    """
    try:
        evidence.image.open()

        image_bytes = evidence.image.read()

        evidence.image.close()

    except Exception as exc:
        raise EvidenceAIAnalysisError(
            "Unable to read the evidence image."
        ) from exc

    try:
        provider = GeminiProvider()

        prompt = build_evidence_prompt(
            evidence.complaint,
            evidence,
        )

        response_text = provider.analyze_image(
            prompt=prompt,
            image_bytes=image_bytes,
            mime_type=evidence.content_type,
        )

        try:
            parsed_output = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise EvidenceAIAnalysisError(
                "Gemini returned invalid JSON for evidence analysis."
            ) from exc

        validated_output = validate_evidence_ai_output(
            parsed_output
        )

    except (
        AIProviderError,
        EvidenceAIValidationError,
    ) as exc:
        raise EvidenceAIAnalysisError(
            str(exc)
        ) from exc

    evidence.analysis_completed = True
    evidence.evidence_type = validated_output[
        "evidence_type"
    ]
    evidence.observations = validated_output[
        "observations"
    ]
    evidence.severity_score = validated_output[
        "severity_score"
    ]
    evidence.confidence_score = validated_output[
        "confidence_score"
    ]
    evidence.complaint_consistency = validated_output[
        "complaint_consistency"
    ]
    evidence.analysis_explanation = validated_output[
        "analysis_explanation"
    ]
    evidence.analysis_model = provider.model_name
    evidence.analyzed_at = datetime.now(
        timezone.utc
    )

    evidence.save(
        update_fields=[
            "analysis_completed",
            "evidence_type",
            "observations",
            "severity_score",
            "confidence_score",
            "complaint_consistency",
            "analysis_explanation",
            "analysis_model",
            "analyzed_at",
        ]
    )

    return evidence