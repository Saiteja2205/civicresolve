from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCitizenUser
from complaints.models import Complaint, ComplaintAssignment
from complaints.services.complaint_service import (
    change_complaint_status,
)


class ComplaintReopenView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsCitizenUser,
    ]

    @transaction.atomic
    def post(self, request, complaint_id):
        try:
            complaint = Complaint.objects.select_related(
                "user",
                "category",
                "category__department",
            ).get(
                id=complaint_id,
                user=request.user,
            )
        except Complaint.DoesNotExist:
            return Response(
                {
                    "detail": "Complaint not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if complaint.status != Complaint.Status.RESOLVED:
            return Response(
                {
                    "detail": (
                        "Only resolved complaints "
                        "can be reopened."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        comment = str(
            request.data.get(
                "comment",
                "",
            )
        ).strip()

        if len(comment) < 10:
            return Response(
                {
                    "detail": (
                        "Please explain why the "
                        "complaint needs to be reopened "
                        "using at least 10 characters."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        active_assignment = (
            ComplaintAssignment.objects
            .select_related(
                "officer",
                "department",
            )
            .filter(
                complaint=complaint,
                unassigned_at__isnull=True,
            )
            .first()
        )

        officer_email = (
            active_assignment.officer.email
            if active_assignment
            else None
        )

        try:
            complaint = change_complaint_status(
                complaint=complaint,
                new_status=Complaint.Status.REOPENED,
                changed_by=request.user,
                comment=(
                    "Citizen requested reopening: "
                    f"{comment}."
                ),
            )

            if active_assignment:
                complaint = change_complaint_status(
                    complaint=complaint,
                    new_status=Complaint.Status.ASSIGNED,
                    changed_by=request.user,
                    comment=(
                        "Reopened complaint returned to "
                        f"assigned officer {officer_email}."
                    ),
                )

                detail = (
                    "Complaint reopened and returned "
                    "to the assigned officer."
                )
            else:
                detail = (
                    "Complaint reopened and is waiting "
                    "for reassignment."
                )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": detail,
                "complaint_id": complaint.id,
                "ticket_number": complaint.ticket_number,
                "status": complaint.status,
                "assigned_officer": officer_email,
            },
            status=status.HTTP_200_OK,
        )