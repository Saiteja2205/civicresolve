from organizations.models import Category, Department


def build_complaint_analysis_prompt(complaint):
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

Analyze the following citizen complaint.

The complaint may be written in English or another language.

First identify the primary language of the original complaint.

Then create a faithful English translation or normalization
of the original title and description.

The English representation must preserve the original meaning.
Do not invent facts, locations, people, events, severity,
causes, or other information that is not present in the
original complaint.

The original citizen text must never be modified.

After creating the English representation, use the meaning of
the complaint to determine the most appropriate category,
department, priority, urgency, confidence, summary, and
concise decision explanation.

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
    "detected_language": "English",
    "english_title": "Faithful English translation or normalization of the original title.",
    "english_description": "Faithful English translation or normalization of the original description.",
    "summary": "A concise summary of the complaint.",
    "explanation": "A concise explanation of the main factors supporting the category and priority decision.",
    "predicted_category": 0,
    "predicted_department": 0,
    "predicted_priority": "LOW",
    "urgency_score": 0,
    "confidence_score": 0
}}

RULES:

1. detected_language must identify the primary language used
   in the original complaint title and description.

2. Use a common human-readable language name such as English,
   Telugu, Hindi, Tamil, Kannada, Malayalam, Bengali, Marathi,
   Urdu, or another appropriate language name.

3. english_title must faithfully translate or normalize the
   original title into English.

4. english_description must faithfully translate or normalize
   the original description into English.

5. Do not invent facts during translation or normalization.

6. If the original complaint is already in English, detected_language
   must be English and the English title and description should
   preserve the original meaning.

7. summary must clearly describe the main issue.

8. explanation must be concise and factual.

9. Do not provide hidden reasoning, chain-of-thought,
   internal deliberation, or step-by-step reasoning.

10. explanation should normally be one or two sentences.

11. predicted_category MUST be the ID of the most appropriate
    category from the AVAILABLE CATEGORIES list.

12. predicted_department MUST be the ID of the department
    responsible for the selected category.

13. predicted_category MUST NOT be null.

14. predicted_department MUST NOT be null.

15. The predicted_category and predicted_department must use
    only IDs that exist in the lists provided above.

16. The selected category's department_id must match
    predicted_department.

17. Do not invent category IDs or department IDs.

18. Use the citizen-selected category as useful context,
    but independently evaluate the complaint description.

19. If the complaint clearly belongs to another category,
    select the more appropriate category from the available
    categories.

20. predicted_priority must be exactly one of:
    LOW
    MEDIUM
    HIGH
    CRITICAL

21. urgency_score must be a number between 0 and 100.

22. confidence_score must be a number between 0 and 100.

23. Consider the impact, severity, affected users, duration,
    safety implications, and urgency when assigning priority
    and urgency_score.

24. Do not include markdown.

25. Do not include explanations outside the JSON object.

26. Always select the best available category.

27. Always select the best available department.

28. Keep the explanation suitable for display to a citizen,
    officer, or administrator.

Return only the JSON object.
"""

    return prompt