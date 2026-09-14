from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminUserRole

from complaints.services.ai_benchmark_cases import (
    BENCHMARK_CASES,
)
from complaints.services.ai_evaluation_service import (
    run_evaluation,
)


class AIEvaluationView(APIView):
    """
    Admin-only API endpoint for running the
    CivicResolve AI benchmark.
    """

    permission_classes = [
        IsAuthenticated,
        IsAdminUserRole,
    ]

    def post(self, request):
        try:
            report = run_evaluation(
                BENCHMARK_CASES
            )

            return Response(
                report,
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            return Response(
                {
                    "detail": (
                        "AI benchmark execution failed: "
                        f"{exc}"
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )