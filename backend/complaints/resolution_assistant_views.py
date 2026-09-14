from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from complaints.models import Complaint
from complaints.services.resolution_assistant_service import (
    ResolutionAssistantError,
    generate_resolution_assistant,
)


class ComplaintResolutionAssistantView(APIView):
    """
    Generate an AI-assisted resolution draft.

    Administrators can use the assistant for any complaint.

    Officers can use it only for complaints that are
    currently assigned to them.

    Citizens cannot use the officer resolution assistant.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def post(
        self,
        request,
        complaint_id,
    ):
        user = request.user

        if user.role == User.Role.USER:
            return Response(
                {
                    "detail": (
                        "The AI resolution assistant is "
                        "available only to administrators "
                        "and assigned officers."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        complaint = (
            Complaint.objects
            .select_related(
                "category",
                "category__department",
            )
            .filter(id=complaint_id)
            .first()
        )

        if complaint is None:
            return Response(
                {
                    "detail": "Complaint not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.role == User.Role.OFFICER:
            is_assigned = (
                complaint.assignments
                .filter(
                    officer=user,
                    unassigned_at__isnull=True,
                )
                .exists()
            )

            if not is_assigned:
                return Response(
                    {
                        "detail": (
                            "You can use the AI resolution "
                            "assistant only for complaints "
                            "currently assigned to you."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        try:
            result = generate_resolution_assistant(
                complaint_id=complaint.id
            )

        except ResolutionAssistantError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )