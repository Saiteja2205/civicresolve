from organizations.models import Category, Department


def build_complaint_analysis_prompt(complaint):
    """
    Build a structured prompt for AI-based complaint analysis.

    The prompt includes the actual categories and departments
    available in the CivicResolve database so that the AI can
    return valid database IDs.
    """

    departments = list(
        Department.objects
        .filter(is_active=True)
        .values("id", "name")
        .order_by("id")
    )

    categories = list(
        Category.objects
        .filter(
            is_active=True,
            department__is_active=True,
        )
        .values(
            "id",
            "name",
            "department_id",
        )
        .order_by("id")
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

    selected_category = (
        complaint.category
        if complaint.category_id
        else None
    )

    selected_category_text = (
        (
            f"Citizen-selected category: "
            f"ID {selected_category.id} - "
            f"{selected_category.name} "
            f"(Department ID: "
            f"{selected_category.department_id})"
        )
        if selected_category
        else "Citizen-selected category: Not provided"
    )

    prompt = f"""
You are the complaint analysis engine for CivicResolve.

Analyze the following citizen complaint and determine the
most appropriate category, department, priority, urgency,
confidence, and a concise decision explanation.

COMPLAINT TITLE:
{complaint.title}

COMPLAINT DESCRIPTION:
{complaint.description}

LOCATION:
{complaint.location or "Not provided"}

{selected_category_text}

AVAILABLE DEPARTMENTS:
{department_lines}

AVAILABLE CATEGORIES:
{category_lines}

Your task is to analyze the complaint and return a structured
JSON object.

Return ONLY valid JSON.

The JSON must contain exactly these fields:
{{
    "summary": "A concise summary of the complaint.",
    "explanation": "A concise explanation of the main factors supporting the category and priority decision.",
    "predicted_category": 0,
    "predicted_department": 0,
    "predicted_priority": "LOW",
    "urgency_score": 0,
    "confidence_score": 0
}}

RULES:

1. summary must clearly describe the main issue.

2. explanation must be concise and factual. Explain the
   important complaint characteristics that support the
   predicted category and priority.

3. Do not provide hidden reasoning, chain-of-thought,
   internal deliberation, or step-by-step reasoning.

4. explanation should normally be one or two sentences.

5. predicted_category MUST be the ID of the most appropriate
   category from the AVAILABLE CATEGORIES list.

6. predicted_department MUST be the ID of the department
   responsible for the selected category.

7. predicted_category MUST NOT be null.

8. predicted_department MUST NOT be null.

9. The predicted_category and predicted_department must use
   only IDs that exist in the lists provided above.

10. The selected category's department_id must match
    predicted_department.

11. Do not invent category IDs or department IDs.

12. Use the citizen-selected category as useful context,
    but independently evaluate the complaint description.
    If the complaint clearly belongs to another category,
    select the more appropriate category from the available
    categories.

13. predicted_priority must be exactly one of:
    LOW
    MEDIUM
    HIGH
    CRITICAL

14. urgency_score must be a number between 0 and 100.

15. confidence_score must be a number between 0 and 100.

16. Consider the impact, severity, affected users, duration,
    safety implications, and urgency when assigning priority
    and urgency_score.

17. Do not include markdown.

18. Do not include explanations outside the JSON object.

19. Always select the best available category.

20. Always select the best available department.

21. Keep the explanation suitable for display to a citizen,
    officer, or administrator.

Return only the JSON object.
"""

    return prompt