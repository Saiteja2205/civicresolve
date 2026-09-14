from unittest.mock import patch

from django.test import TestCase

from complaints.models import (
    Complaint,
    ComplaintAnalysis,
)
from complaints.services.ai_evaluation_service import (
    EvaluationCase,
    calculate_accuracy,
    calculate_urgency_mae,
    evaluate_prediction,
    run_evaluation,
)
from accounts.models import User
from organizations.models import Category, Department


class FakeAnalysis:
    def __init__(
        self,
        category_name,
        priority,
        urgency,
    ):
        self.predicted_category = type(
            "FakeCategory",
            (),
            {
                "name": category_name,
            },
        )()

        self.predicted_priority = priority
        self.urgency_score = urgency


class AIEvaluationUnitTests(TestCase):
    def test_calculate_accuracy(self):
        self.assertEqual(
            calculate_accuracy(8, 10),
            80.0,
        )

    def test_zero_accuracy(self):
        self.assertEqual(
            calculate_accuracy(0, 0),
            0.0,
        )

    def test_calculate_urgency_mae(self):
        result_1 = type(
            "Result",
            (),
            {
                "urgency_absolute_error": 10.0,
            },
        )()

        result_2 = type(
            "Result",
            (),
            {
                "urgency_absolute_error": 20.0,
            },
        )()

        self.assertEqual(
            calculate_urgency_mae(
                [result_1, result_2]
            ),
            15.0,
        )

    def test_evaluate_prediction_passes(self):
        case = EvaluationCase(
            name="test",
            title="Water leakage",
            description=(
                "There is water leakage near Block A."
            ),
            category_name="Water Leakage",
            expected_priority="HIGH",
            expected_urgency=70,
        )

        analysis = FakeAnalysis(
            category_name="Water Leakage",
            priority="HIGH",
            urgency=65,
        )

        result = evaluate_prediction(
            case,
            analysis,
        )

        self.assertTrue(
            result.category_correct
        )

        self.assertTrue(
            result.priority_correct
        )

        self.assertEqual(
            result.urgency_absolute_error,
            5.0,
        )

        self.assertTrue(
            result.passed
        )

    def test_evaluate_prediction_fails_category(self):
        case = EvaluationCase(
            name="test",
            title="Water leakage",
            description=(
                "There is water leakage near Block A."
            ),
            category_name="Water Leakage",
            expected_priority="HIGH",
            expected_urgency=70,
        )

        analysis = FakeAnalysis(
            category_name="Road Damage",
            priority="HIGH",
            urgency=70,
        )

        result = evaluate_prediction(
            case,
            analysis,
        )

        self.assertFalse(
            result.category_correct
        )

        self.assertFalse(
            result.passed
        )

    def test_evaluate_prediction_fails_large_urgency_error(
        self,
    ):
        case = EvaluationCase(
            name="test",
            title="Water leakage",
            description=(
                "There is water leakage near Block A."
            ),
            category_name="Water Leakage",
            expected_priority="HIGH",
            expected_urgency=70,
        )

        analysis = FakeAnalysis(
            category_name="Water Leakage",
            priority="HIGH",
            urgency=20,
        )

        result = evaluate_prediction(
            case,
            analysis,
        )

        self.assertEqual(
            result.urgency_absolute_error,
            50.0,
        )

        self.assertFalse(
            result.passed
        )


class AIEvaluationIntegrationTests(
    TestCase
):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(
            name="Evaluation Department"
        )

        cls.category = Category.objects.create(
            name="Evaluation Category",
            department=cls.department,
        )

        cls.user = User.objects.create_user(
            email="evaluation.admin@test.local",
            password="TestPass123!",
            role=User.Role.ADMIN,
            is_active=True,
        )

    @patch(
        "complaints.services.ai_evaluation_service."
        "create_ai_analysis"
    )
    def test_benchmark_case_is_rolled_back(
        self,
        mock_create_analysis,
    ):
        mock_create_analysis.return_value = (
            FakeAnalysis(
                category_name="Evaluation Category",
                priority="MEDIUM",
                urgency=50,
            )
        )

        case = EvaluationCase(
            name="rollback-test",
            title="Evaluation complaint",
            description=(
                "This complaint exists only "
                "for benchmark testing."
            ),
            category_name="Evaluation Category",
            expected_priority="MEDIUM",
            expected_urgency=50,
        )

        before_count = Complaint.objects.count()

        result = run_evaluation(
            [case]
        )

        after_count = Complaint.objects.count()

        self.assertEqual(
            before_count,
            after_count,
        )

        self.assertEqual(
            len(result["results"]),
            1,
        )

        self.assertTrue(
            result["results"][0]["passed"]
        )

    @patch(
        "complaints.services.ai_evaluation_service."
        "create_ai_analysis"
    )
    def test_benchmark_report_contains_metrics(
        self,
        mock_create_analysis,
    ):
        mock_create_analysis.return_value = (
            FakeAnalysis(
                category_name="Evaluation Category",
                priority="MEDIUM",
                urgency=50,
            )
        )

        case = EvaluationCase(
            name="metrics-test",
            title="Evaluation complaint",
            description=(
                "This complaint exists only "
                "for benchmark testing."
            ),
            category_name="Evaluation Category",
            expected_priority="MEDIUM",
            expected_urgency=50,
        )

        report = run_evaluation(
            [case]
        )

        self.assertIn(
            "category_accuracy_percent",
            report,
        )

        self.assertIn(
            "priority_accuracy_percent",
            report,
        )

        self.assertIn(
            "urgency_mae",
            report,
        )

        self.assertIn(
            "overall_pass_rate_percent",
            report,
        )

        self.assertEqual(
            report["total_cases"],
            1,
        )

        self.assertEqual(
            report["passed_cases"],
            1,
        )

    def test_empty_benchmark(self):
        report = run_evaluation([])

        self.assertEqual(
            report["total_cases"],
            0,
        )

        self.assertEqual(
            report["passed_cases"],
            0,
        )

        self.assertEqual(
            report["urgency_mae"],
            0.0,
        )