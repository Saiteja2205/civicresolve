from dataclasses import dataclass

from django.db import transaction

from accounts.models import User
from complaints.models import Complaint
from complaints.services.ai_analysis_service import (
    create_ai_analysis,
)
from complaints.services.ai_provider import (
    AIProviderError,
)
from organizations.models import Category


@dataclass(frozen=True)
class EvaluationCase:
    """
    Human-labelled benchmark case.
    """

    name: str
    title: str
    description: str
    category_name: str
    expected_priority: str
    expected_urgency: float


@dataclass
class EvaluationResult:
    """
    Evaluation result for one benchmark case.
    """

    name: str
    expected_category: str
    predicted_category: str | None
    category_correct: bool

    expected_priority: str
    predicted_priority: str | None
    priority_correct: bool

    expected_urgency: float
    predicted_urgency: float | None
    urgency_absolute_error: float | None

    passed: bool
    error: str | None = None


def calculate_accuracy(
    correct,
    total,
):
    """
    Calculate percentage accuracy.
    """

    if total == 0:
        return 0.0

    return round(
        (correct / total) * 100,
        2,
    )


def calculate_urgency_mae(
    results,
):
    """
    Calculate Mean Absolute Error for urgency predictions.
    """

    errors = [
        result.urgency_absolute_error
        for result in results
        if result.urgency_absolute_error is not None
    ]

    if not errors:
        return 0.0

    return round(
        sum(errors) / len(errors),
        2,
    )


def evaluate_prediction(
    case,
    analysis,
):
    """
    Compare an AI prediction against the human-labelled
    expected values.
    """

    predicted_category = None

    if analysis.predicted_category:
        predicted_category = (
            analysis.predicted_category.name
        )

    predicted_priority = (
        analysis.predicted_priority
        if analysis.predicted_priority
        else None
    )

    predicted_urgency = None

    if analysis.urgency_score is not None:
        predicted_urgency = float(
            analysis.urgency_score
        )

    category_correct = (
        predicted_category == case.category_name
    )

    priority_correct = (
        predicted_priority == case.expected_priority
    )

    urgency_absolute_error = None

    if predicted_urgency is not None:
        urgency_absolute_error = round(
            abs(
                predicted_urgency
                - case.expected_urgency
            ),
            2,
        )

    passed = (
        category_correct
        and priority_correct
        and urgency_absolute_error is not None
        and urgency_absolute_error <= 15
    )

    return EvaluationResult(
        name=case.name,
        expected_category=case.category_name,
        predicted_category=predicted_category,
        category_correct=category_correct,
        expected_priority=case.expected_priority,
        predicted_priority=predicted_priority,
        priority_correct=priority_correct,
        expected_urgency=case.expected_urgency,
        predicted_urgency=predicted_urgency,
        urgency_absolute_error=(
            urgency_absolute_error
        ),
        passed=passed,
    )


def _get_benchmark_user():
    """
    Obtain a safe user for temporary benchmark complaints.

    The user is never modified by the evaluation.
    """

    user = (
        User.objects
        .filter(
            role=User.Role.ADMIN,
            is_active=True,
        )
        .order_by("id")
        .first()
    )

    if user is None:
        raise AIProviderError(
            "No active administrator exists for "
            "AI benchmark execution."
        )

    return user


def _get_category(category_name):
    """
    Resolve a benchmark category from the active database.
    """

    category = (
        Category.objects
        .filter(
            name=category_name,
            is_active=True,
            department__is_active=True,
        )
        .select_related("department")
        .first()
    )

    if category is None:
        raise AIProviderError(
            f"Benchmark category '{category_name}' "
            "does not exist or is inactive."
        )

    return category


def _run_single_case(case):
    """
    Execute one benchmark case inside a transaction.

    The transaction is always rolled back so the temporary
    complaint and generated analysis are never persisted.
    """

    try:
        with transaction.atomic():
            user = _get_benchmark_user()

            category = _get_category(
                case.category_name
            )

            complaint = Complaint.objects.create(
                user=user,
                category=category,
                title=case.title,
                description=case.description,
                status=Complaint.Status.SUBMITTED,
                priority=Complaint.Priority.MEDIUM,
            )

            analysis = create_ai_analysis(
                complaint=complaint,
            )

            result = evaluate_prediction(
                case=case,
                analysis=analysis,
            )

            transaction.set_rollback(True)

            return result

    except AIProviderError as exc:
        return EvaluationResult(
            name=case.name,
            expected_category=case.category_name,
            predicted_category=None,
            category_correct=False,
            expected_priority=case.expected_priority,
            predicted_priority=None,
            priority_correct=False,
            expected_urgency=case.expected_urgency,
            predicted_urgency=None,
            urgency_absolute_error=None,
            passed=False,
            error=str(exc),
        )

    except Exception as exc:
        return EvaluationResult(
            name=case.name,
            expected_category=case.category_name,
            predicted_category=None,
            category_correct=False,
            expected_priority=case.expected_priority,
            predicted_priority=None,
            priority_correct=False,
            expected_urgency=case.expected_urgency,
            predicted_urgency=None,
            urgency_absolute_error=None,
            passed=False,
            error=str(exc),
        )


def run_evaluation(cases):
    """
    Run the complete AI benchmark.
    """

    if not cases:
        return {
            "total_cases": 0,
            "category_accuracy_percent": 0.0,
            "priority_accuracy_percent": 0.0,
            "urgency_mae": 0.0,
            "overall_pass_rate_percent": 0.0,
            "passed_cases": 0,
            "failed_cases": 0,
            "results": [],
        }

    results = [
        _run_single_case(case)
        for case in cases
    ]

    total = len(results)

    category_correct = sum(
        result.category_correct
        for result in results
    )

    priority_correct = sum(
        result.priority_correct
        for result in results
    )

    passed_cases = sum(
        result.passed
        for result in results
    )

    return {
        "total_cases": total,
        "category_accuracy_percent": calculate_accuracy(
            category_correct,
            total,
        ),
        "priority_accuracy_percent": calculate_accuracy(
            priority_correct,
            total,
        ),
        "urgency_mae": calculate_urgency_mae(
            results
        ),
        "overall_pass_rate_percent": calculate_accuracy(
            passed_cases,
            total,
        ),
        "passed_cases": passed_cases,
        "failed_cases": total - passed_cases,
        "results": [
            {
                "name": result.name,
                "expected_category": (
                    result.expected_category
                ),
                "predicted_category": (
                    result.predicted_category
                ),
                "category_correct": (
                    result.category_correct
                ),
                "expected_priority": (
                    result.expected_priority
                ),
                "predicted_priority": (
                    result.predicted_priority
                ),
                "priority_correct": (
                    result.priority_correct
                ),
                "expected_urgency": (
                    result.expected_urgency
                ),
                "predicted_urgency": (
                    result.predicted_urgency
                ),
                "urgency_absolute_error": (
                    result.urgency_absolute_error
                ),
                "passed": result.passed,
                "error": result.error,
            }
            for result in results
        ],
    }