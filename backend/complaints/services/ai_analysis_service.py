import json

from django.db import transaction

from complaints.models import ComplaintAnalysis
from complaints.services.ai_output_validator import (
    validate_ai_output,
)
from complaints.services.ai_prompt import (
    build_complaint_analysis_prompt,
)
from complaints.services.ai_provider import (
    AIProviderError,
    GeminiProvider,
)
from organizations.models import Category


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


def apply_category_fallback(
    complaint,
    validated_output,
):
    """
    If AI does not provide a category, use the category
    explicitly selected by the citizen as a safe routing
    fallback.

    AI predictions remain authoritative whenever they are
    valid.
    """

    if validated_output["predicted_category"] is not None:
        return validated_output

    if not complaint.category_id:
        raise AIProviderError(
            "AI did not predict a category and the complaint "
            "does not contain a selected category."
        )

    category = (
        Category.objects
        .filter(
            id=complaint.category_id,
            is_active=True,
            department__is_active=True,
        )
        .select_related("department")
        .first()
    )

    if category is None:
        raise AIProviderError(
            "The complaint's selected category is invalid "
            "or inactive."
        )

    validated_output["predicted_category"] = (
        category.id
    )

    validated_output["predicted_department"] = (
        category.department_id
    )

    return validated_output


@transaction.atomic
def create_ai_analysis(
    complaint,
    ai_output=None,
):
    """
    Create or update the AI analysis for a complaint.

    If ai_output is provided, it is used directly for testing.

    If ai_output is not provided, Gemini generates the analysis.

    The AI-predicted category and department are validated
    against the active CivicResolve database.

    If AI returns no category, the citizen-selected category
    is used as a safe routing fallback.

    The validated AI priority is applied to the complaint so
    downstream SLA calculation uses the AI decision.
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

    validated_output = apply_category_fallback(
        complaint,
        validated_output,
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
            },
        )
    )

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