def build_complaint_analysis_prompt(complaint):
    """
    Build a structured prompt for AI-based complaint analysis.
    """

    prompt = f"""
You are the complaint analysis engine for CivicResolve.

Analyze the following citizen complaint.

COMPLAINT TITLE:
{complaint.title}

COMPLAINT DESCRIPTION:
{complaint.description}

LOCATION:
{complaint.location or "Not provided"}

Your task is to analyze the complaint and return a structured JSON object.

Return ONLY valid JSON.

The JSON must contain exactly these fields:

{{
    "summary": "A concise summary of the complaint.",
    "predicted_category": null,
    "predicted_department": null,
    "predicted_priority": "LOW",
    "urgency_score": 0,
    "confidence_score": 0
}}

RULES:

1. summary must clearly describe the main issue.
2. predicted_category must contain the ID of the most appropriate complaint category.
3. predicted_department must contain the ID of the department responsible for handling the complaint.
4. predicted_priority must be exactly one of:
   LOW
   MEDIUM
   HIGH
   CRITICAL

5. urgency_score must be a number between 0 and 100.
6. confidence_score must be a number between 0 and 100.
7. Do not invent category or department IDs.
8. If you cannot determine a category or department reliably, return null for that field.
9. Do not include markdown.
10. Do not include explanations outside the JSON object.

Return only the JSON object.
"""

    return prompt