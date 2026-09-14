import json

from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from complaints.services.ai_benchmark_cases import (
    BENCHMARK_CASES,
)
from complaints.services.ai_evaluation_service import (
    run_evaluation,
)


class Command(BaseCommand):
    help = (
        "Run the CivicResolve AI classification "
        "evaluation benchmark."
    )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                "Running CivicResolve AI benchmark..."
            )
        )

        try:
            report = run_evaluation(
                BENCHMARK_CASES
            )

        except Exception as exc:
            raise CommandError(
                f"Benchmark failed: {exc}"
            ) from exc

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "AI EVALUATION RESULTS"
            )
        )
        self.stdout.write("=" * 60)

        self.stdout.write(
            f"Total cases: "
            f"{report['total_cases']}"
        )

        self.stdout.write(
            f"Category accuracy: "
            f"{report['category_accuracy_percent']}%"
        )

        self.stdout.write(
            f"Priority accuracy: "
            f"{report['priority_accuracy_percent']}%"
        )

        self.stdout.write(
            f"Urgency MAE: "
            f"{report['urgency_mae']}"
        )

        self.stdout.write(
            f"Overall pass rate: "
            f"{report['overall_pass_rate_percent']}%"
        )

        self.stdout.write(
            f"Passed cases: "
            f"{report['passed_cases']}"
        )

        self.stdout.write(
            f"Failed cases: "
            f"{report['failed_cases']}"
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "PER-CASE RESULTS"
            )
        )
        self.stdout.write("=" * 60)

        for result in report["results"]:
            status = (
                "PASS"
                if result["passed"]
                else "FAIL"
            )

            if result["passed"]:
                status_text = self.style.SUCCESS(
                    f"[{status}]"
                )
            else:
                status_text = self.style.ERROR(
                    f"[{status}]"
                )

            self.stdout.write(
                f"{status_text} "
                f"{result['name']}"
            )

            self.stdout.write(
                f"  Category: "
                f"{result['expected_category']} -> "
                f"{result['predicted_category']}"
            )

            category_status = (
                "correct"
                if result["category_correct"]
                else "incorrect"
            )

            self.stdout.write(
                f"  Category result: "
                f"{category_status}"
            )

            self.stdout.write(
                f"  Priority: "
                f"{result['expected_priority']} -> "
                f"{result['predicted_priority']}"
            )

            priority_status = (
                "correct"
                if result["priority_correct"]
                else "incorrect"
            )

            self.stdout.write(
                f"  Priority result: "
                f"{priority_status}"
            )

            self.stdout.write(
                f"  Urgency: "
                f"{result['expected_urgency']} -> "
                f"{result['predicted_urgency']}"
            )

            if (
                result["urgency_absolute_error"]
                is not None
            ):
                self.stdout.write(
                    f"  Urgency absolute error: "
                    f"{result['urgency_absolute_error']}"
                )

            if result["error"]:
                self.stdout.write(
                    f"  Error: "
                    f"{result['error']}"
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "JSON REPORT"
            )
        )
        self.stdout.write("=" * 60)

        self.stdout.write(
            json.dumps(
                report,
                indent=2,
            )
        )