import json

from django.db import transaction

from complaints.models import ComplaintAnalysis
from complaints.services.ai_output_validator import validate_ai_output
from complaints.services.ai_prompt import build_complaint_analysis_prompt
from complaints.services.ai_provider import (
    AIProviderError,
    GeminiProvider,
)


def parse_ai_response(response_text):
    """
    Convert the AI's JSON response text into a Python dictionary.
    """

    if not isinstance(response_text, str):
        raise AIProviderError(
            "AI response must be text."
        )

    response_text = response_text.strip()

    if not response_text:
        raise AIProviderError(
            "AI response is empty."
        )

    # Handle a response that may still contain markdown
    # code fences, even though JSON output was requested.
    if response_text.startswith("```"):
        lines = response_text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        response_text = "\n".join(lines).strip()

    try:
        data = json.loads(response_text)

    except json.JSONDecodeError as exc:
        raise AIProviderError(
            "AI returned invalid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise AIProviderError(
            "AI response must be a JSON object."
        )

    return data


@transaction.atomic
def create_ai_analysis(complaint, ai_output=None):
    """
    Create or update the AI analysis for a complaint.

    If ai_output is provided, it is used directly for testing.

    If ai_output is not provided, Gemini generates the analysis.

    After successful validation, the AI-predicted priority is
    applied to the complaint so downstream SLA calculation
    uses the AI decision.
    """

    provider = None

    if ai_output is None:
        prompt = build_complaint_analysis_prompt(
            complaint
        )

        provider = GeminiProvider()

        response_text = provider.analyze_complaint(
            prompt
        )

        ai_output = parse_ai_response(
            response_text
        )

    validated_output = validate_ai_output(
        ai_output
    )

    analysis, created = (
        ComplaintAnalysis.objects.update_or_create(
            complaint=complaint,
            defaults={
                "summary": validated_output["summary"],
                "predicted_category_id": (
                    validated_output[
                        "predicted_category"
                    ]
                ),
                "predicted_department_id": (
                    validated_output[
                        "predicted_department"
                    ]
                ),
                "predicted_priority": (
                    validated_output[
                        "predicted_priority"
                    ]
                ),
                "urgency_score": (
                    validated_output[
                        "urgency_score"
                    ]
                ),
                "confidence_score": (
                    validated_output[
                        "confidence_score"
                    ]
                ),
                "model_name": (
                    provider.model_name
                    if provider is not None
                    else "CivicResolve-AI-Manual-Test"
                ),
            }
        )
    )

    # Apply the validated AI priority to the actual complaint.
    complaint.priority = validated_output[
        "predicted_priority"
    ]

    complaint.save(
        update_fields=[
            "priority",
            "updated_at",
        ]
    )

    return analysis