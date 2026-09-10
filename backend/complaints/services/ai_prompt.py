from organizations.models import Category, Department


def build_complaint_analysis_prompt(complaint):
    """
    Build a structured prompt for AI-based complaint analysis.

    The prompt includes the actual categories and departments
    available in the CivicResolve database so that the AI can
    return valid database IDs.
    """

    departments = list(
        Department.objects.values("id", "name")
        .order_by("id")
    )

    categories = list(
        Category.objects.values(
            "id",
            "name",
            "department_id",
        ).order_by("id")
    )

    department_lines = "\n".join(
        f'- ID {department["id"]}: {department["name"]}'
        for department in departments
    )

    category_lines = "\n".join(
        (
            f'- ID {category["id"]}: {category["name"]} '
            f'(Department ID: {category["department_id"]})'
        )
        for category in categories
    )

    prompt = f"""
You are the complaint analysis engine for CivicResolve.

Analyze the following citizen complaint.

COMPLAINT TITLE:
{complaint.title}

COMPLAINT DESCRIPTION:
{complaint.description}

LOCATION:
{complaint.location or "Not provided"}

AVAILABLE DEPARTMENTS:
{department_lines}

AVAILABLE CATEGORIES:
{category_lines}

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

2. predicted_category must be the ID of the most appropriate
   category from the AVAILABLE CATEGORIES list.

3. predicted_department must be the ID of the department responsible
   for the selected category.

4. The predicted_category and predicted_department must use only
   IDs that exist in the lists provided above.

5. The selected category's department_id must match
   predicted_department.

6. Do not invent category IDs or department IDs.

7. If no category can be determined reliably, return null for
   predicted_category and predicted_department.

8. predicted_priority must be exactly one of:
   LOW
   MEDIUM
   HIGH
   CRITICAL

9. urgency_score must be a number between 0 and 100.

10. confidence_score must be a number between 0 and 100.

11. Consider the impact, severity, affected users, duration,
    safety implications, and urgency when assigning priority
    and urgency_score.

12. Do not include markdown.

13. Do not include explanations outside the JSON object.

Return only the JSON object.
"""

    return prompt