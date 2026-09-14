import json

from complaints.models import Complaint
from complaints.services.ai_provider import (
    AIProviderError,
    GeminiProvider,
)


class ResolutionAssistantError(Exception):
    """
    Raised when the AI resolution assistant cannot
    generate a valid response.
    """

    pass


def build_resolution_assistant_prompt(
    complaint,
    history,
    evidence,
    sla,
):
    """
    Build the structured prompt used by the AI resolution assistant.
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

    ai_analysis = getattr(
        complaint,
        "analysis",
        None,
    )

    if ai_analysis:
        ai_summary = ai_analysis.summary or "Not available"
        ai_explanation = (
            ai_analysis.explanation
            or "Not available"
        )
        ai_priority = (
            ai_analysis.predicted_priority
            or "Not available"
        )
        ai_urgency = (
            str(ai_analysis.urgency_score)
            if ai_analysis.urgency_score is not None
            else "Not available"
        )
        ai_confidence = (
            str(ai_analysis.confidence_score)
            if ai_analysis.confidence_score is not None
            else "Not available"
        )
    else:
        ai_summary = "Not available"
        ai_explanation = "Not available"
        ai_priority = "Not available"
        ai_urgency = "Not available"
        ai_confidence = "Not available"

    history_lines = []

    for item in history:
        changed_by = (
            item.changed_by.email
            if item.changed_by
            else "System"
        )

        history_lines.append(
            f"- {item.created_at.isoformat()} | "
            f"{item.old_status or 'NEW'} -> "
            f"{item.new_status} | "
            f"By: {changed_by} | "
            f"Comment: {item.comment or 'None'}"
        )

    history_text = (
        "\n".join(history_lines)
        if history_lines
        else "No complaint history available."
    )

    evidence_lines = []

    for item in evidence:
        evidence_lines.append(
            f"- File: {item.original_filename} | "
            f"Type: {item.get_evidence_type_display() or 'Unknown'} | "
            f"Analysis completed: "
            f"{item.analysis_completed} | "
            f"Observations: "
            f"{item.observations or 'None'} | "
            f"Severity: "
            f"{item.severity_score if item.severity_score is not None else 'N/A'} | "
            f"Confidence: "
            f"{item.confidence_score if item.confidence_score is not None else 'N/A'} | "
            f"Consistent with complaint: "
            f"{item.complaint_consistency if item.complaint_consistency is not None else 'N/A'}"
        )

    evidence_text = (
        "\n".join(evidence_lines)
        if evidence_lines
        else "No evidence uploaded."
    )

    if sla:
        sla_text = (
            f"Response deadline: {sla.response_deadline.isoformat()}\n"
            f"Resolution deadline: {sla.resolution_deadline.isoformat()}\n"
            f"Response breached: {sla.response_breached}\n"
            f"Resolution breached: {sla.resolution_breached}"
        )
    else:
        sla_text = "SLA information is not available."

    return f"""
You are the AI resolution assistant for CivicResolve,
an intelligent grievance management system.

Your role is to assist a government/public-service officer
in preparing a professional resolution plan and citizen response.

You MUST NOT make the final resolution decision.
You MUST NOT claim that an action has already been completed
unless the supplied information explicitly proves it.

Complaint information:

Ticket number:
{complaint.ticket_number}

Title:
{complaint.title}

Description:
{complaint.description}

Category:
{category_name}

Department:
{department_name}

Current status:
{complaint.status}

Current priority:
{complaint.priority}

Location:
{complaint.location or "Not provided"}

AI complaint summary:
{ai_summary}

AI complaint explanation:
{ai_explanation}

AI predicted priority:
{ai_priority}

AI urgency score:
{ai_urgency}

AI confidence score:
{ai_confidence}

Complaint history:
{history_text}

Evidence analysis:
{evidence_text}

SLA information:
{sla_text}

Return ONLY valid JSON.

Required JSON structure:

{{
  "resolution_draft": "A concise professional draft describing the proposed resolution or next steps for the officer.",
  "recommended_actions": [
    "Specific practical action 1",
    "Specific practical action 2"
  ],
  "citizen_response_draft": "A professional citizen-facing response draft that does not falsely claim completion.",
  "confidence_score": 0,
  "basis": [
    "Complaint description",
    "Complaint history"
  ]
}}

Rules:

1. Use only information provided above.
2. Do not invent inspections, repairs, payments, visits,
   approvals, evidence, officials, dates, or completed actions.
3. Do not state that the complaint is resolved unless the
   supplied information explicitly establishes that.
4. Recommended actions must be practical and relevant to
   the complaint.
5. The citizen response must be professional, clear,
   respectful, and concise.
6. confidence_score must be an integer from 0 to 100.
7. The basis array must contain the main information sources
   used to prepare the recommendation.
8. Keep resolution_draft concise.
9. Keep citizen_response_draft concise.
10. Return no markdown.
11. Return no additional JSON fields.
"""


def generate_resolution_assistant(
    complaint_id,
):
    """
    Generate a validated AI resolution-assistant response
    for one complaint.
    """

    try:
        complaint = (
            Complaint.objects
            .select_related(
                "category",
                "category__department",
                "analysis",
            )
            .prefetch_related(
                "history__changed_by",
                "evidence",
                "sla",
            )
            .get(id=complaint_id)
        )

    except Complaint.DoesNotExist as exc:
        raise ResolutionAssistantError(
            "Complaint not found."
        ) from exc

    history = list(
        complaint.history.all()
    )

    evidence = list(
        complaint.evidence.all()
    )

    sla = getattr(
        complaint,
        "sla",
        None,
    )

    prompt = build_resolution_assistant_prompt(
        complaint=complaint,
        history=history,
        evidence=evidence,
        sla=sla,
    )

    try:
        provider = GeminiProvider()

        response_text = provider.analyze_complaint(
            prompt
        )

    except AIProviderError as exc:
        raise ResolutionAssistantError(
            str(exc)
        ) from exc

    try:
        result = json.loads(response_text)

    except json.JSONDecodeError as exc:
        raise ResolutionAssistantError(
            "Gemini returned invalid JSON for the "
            "resolution assistant."
        ) from exc

    if not isinstance(result, dict):
        raise ResolutionAssistantError(
            "Resolution assistant response must be a JSON object."
        )

    required_fields = {
        "resolution_draft",
        "recommended_actions",
        "citizen_response_draft",
        "confidence_score",
        "basis",
    }

    missing_fields = (
        required_fields - set(result.keys())
    )

    if missing_fields:
        raise ResolutionAssistantError(
            "Resolution assistant response is missing "
            "required fields: "
            + ", ".join(sorted(missing_fields))
        )

    resolution_draft = result[
        "resolution_draft"
    ]

    citizen_response_draft = result[
        "citizen_response_draft"
    ]

    recommended_actions = result[
        "recommended_actions"
    ]

    confidence_score = result[
        "confidence_score"
    ]

    basis = result[
        "basis"
    ]

    if not isinstance(
        resolution_draft,
        str,
    ):
        raise ResolutionAssistantError(
            "resolution_draft must be a string."
        )

    if not isinstance(
        citizen_response_draft,
        str,
    ):
        raise ResolutionAssistantError(
            "citizen_response_draft must be a string."
        )

    if not isinstance(
        recommended_actions,
        list,
    ):
        raise ResolutionAssistantError(
            "recommended_actions must be a list."
        )

    if not recommended_actions:
        raise ResolutionAssistantError(
            "recommended_actions cannot be empty."
        )

    if not all(
        isinstance(item, str)
        and item.strip()
        for item in recommended_actions
    ):
        raise ResolutionAssistantError(
            "Every recommended action must be "
            "a non-empty string."
        )

    if not isinstance(
        basis,
        list,
    ):
        raise ResolutionAssistantError(
            "basis must be a list."
        )

    if not basis:
        raise ResolutionAssistantError(
            "basis cannot be empty."
        )

    if not all(
        isinstance(item, str)
        and item.strip()
        for item in basis
    ):
        raise ResolutionAssistantError(
            "Every basis item must be "
            "a non-empty string."
        )

    try:
        confidence_score = float(
            confidence_score
        )

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ResolutionAssistantError(
            "confidence_score must be a number."
        ) from exc

    if not 0 <= confidence_score <= 100:
        raise ResolutionAssistantError(
            "confidence_score must be between 0 and 100."
        )

    return {
        "complaint": complaint.id,
        "ticket_number": complaint.ticket_number,
        "resolution_draft": (
            resolution_draft.strip()
        ),
        "recommended_actions": [
            item.strip()
            for item in recommended_actions
        ],
        "citizen_response_draft": (
            citizen_response_draft.strip()
        ),
        "confidence_score": confidence_score,
        "basis": [
            item.strip()
            for item in basis
        ],
        "model": provider.model_name,
    }