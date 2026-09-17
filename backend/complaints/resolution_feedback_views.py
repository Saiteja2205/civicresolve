from django.db import transaction

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCitizenUser

from .models import (
    Complaint,
    ComplaintHistory,
    ComplaintResolutionFeedback,
)
from .serializers import ComplaintResolutionFeedbackSerializer


def get_current_resolution_cycle(complaint):
    """
    Return the resolution cycle currently associated with a
    resolved complaint.

    Every transition into RESOLVED represents one completed
    resolution cycle.

    Examples:

        First resolution:
            IN_PROGRESS -> RESOLVED
            cycle = 1

        Reopened and resolved again:
            IN_PROGRESS -> RESOLVED
            cycle = 2
    """

    resolved_count = ComplaintHistory.objects.filter(
        complaint=complaint,
        new_status=Complaint.Status.RESOLVED,
    ).count()

    return max(resolved_count, 1)


class ComplaintResolutionFeedbackView(APIView):
    """
    Citizen Resolution Feedback API.

    GET:
        Return all feedback submitted for a complaint.

    POST:
        Submit feedback for the current resolution cycle.

    Only the citizen who owns the complaint may access
    this endpoint.
    """

    permission_classes = [
        IsAuthenticated,
        IsCitizenUser,
    ]

    def get_complaint(self, complaint_id, user):
        """
        Return the complaint only when it belongs to the
        authenticated citizen.
        """

        return Complaint.objects.filter(
            id=complaint_id,
            user=user,
        ).first()

    def get(self, request, complaint_id):
        """
        Return all resolution feedback submitted by the
        authenticated citizen for this complaint.
        """

        complaint = self.get_complaint(
            complaint_id,
            request.user,
        )

        if complaint is None:
            return Response(
                {
                    "detail": (
                        "Complaint not found or you do not "
                        "have permission to access it."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        feedback = (
            ComplaintResolutionFeedback.objects
            .filter(
                complaint=complaint,
                citizen=request.user,
            )
            .select_related(
                "complaint",
                "citizen",
            )
        )

        current_resolution_cycle = (
            get_current_resolution_cycle(complaint)
        )

        serializer = ComplaintResolutionFeedbackSerializer(
            feedback,
            many=True,
        )

        return Response(
            {
                "complaint_id": complaint.id,
                "ticket_number": complaint.ticket_number,
                "count": feedback.count(),
                "current_resolution_cycle": current_resolution_cycle,
                "feedback": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def post(self, request, complaint_id):
        """
        Submit citizen feedback for the current resolution.

        Feedback is allowed only while the complaint is
        RESOLVED.

        One feedback record is allowed per resolution cycle.
        """

        complaint = (
            Complaint.objects
            .select_for_update()
            .filter(
                id=complaint_id,
                user=request.user,
            )
            .first()
        )

        if complaint is None:
            return Response(
                {
                    "detail": (
                        "Complaint not found or you do not "
                        "have permission to access it."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if complaint.status != Complaint.Status.RESOLVED:
            return Response(
                {
                    "detail": (
                        "Feedback can only be submitted after "
                        "the complaint has been marked as resolved."
                    ),
                    "current_status": complaint.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        resolution_cycle = get_current_resolution_cycle(
            complaint
        )

        existing_feedback = (
            ComplaintResolutionFeedback.objects
            .filter(
                complaint=complaint,
                citizen=request.user,
                resolution_cycle=resolution_cycle,
            )
            .first()
        )

        if existing_feedback is not None:
            serializer = ComplaintResolutionFeedbackSerializer(
                existing_feedback
            )

            return Response(
                {
                    "detail": (
                        "You have already submitted feedback "
                        "for this resolution cycle."
                    ),
                    "feedback": serializer.data,
                },
                status=status.HTTP_409_CONFLICT,
            )

        serializer = ComplaintResolutionFeedbackSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        feedback = serializer.save(
            complaint=complaint,
            citizen=request.user,
            resolution_cycle=resolution_cycle,
        )

        response_serializer = (
            ComplaintResolutionFeedbackSerializer(
                feedback
            )
        )

        return Response(
            {
                "detail": (
                    "Your resolution feedback has been "
                    "submitted successfully."
                ),
                "feedback": response_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class ComplaintResolutionFeedbackDetailView(APIView):
    """
    Retrieve or update feedback belonging to the authenticated
    citizen for a specific feedback record.

    DELETE is intentionally not provided.

    Feedback is treated as part of the complaint's resolution
    history and should remain available for audit purposes.
    """

    permission_classes = [
        IsAuthenticated,
        IsCitizenUser,
    ]

    def get_feedback(self, feedback_id, user):
        """
        Return feedback only when it belongs to the authenticated
        citizen.
        """

        return (
            ComplaintResolutionFeedback.objects
            .select_related(
                "complaint",
                "citizen",
            )
            .filter(
                id=feedback_id,
                citizen=user,
            )
            .first()
        )

    def get(self, request, feedback_id):
        """
        Retrieve one feedback record.
        """

        feedback = self.get_feedback(
            feedback_id,
            request.user,
        )

        if feedback is None:
            return Response(
                {
                    "detail": (
                        "Feedback not found or you do not "
                        "have permission to access it."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ComplaintResolutionFeedbackSerializer(
            feedback
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def patch(self, request, feedback_id):
        """
        Allow the citizen to update the rating/comment for
        their feedback.

        The complaint must still be RESOLVED.

        The resolution cycle cannot be changed.
        """

        feedback = self.get_feedback(
            feedback_id,
            request.user,
        )

        if feedback is None:
            return Response(
                {
                    "detail": (
                        "Feedback not found or you do not "
                        "have permission to modify it."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        complaint = (
            Complaint.objects
            .select_for_update()
            .filter(
                id=feedback.complaint_id,
                user=request.user,
            )
            .first()
        )

        if complaint is None:
            return Response(
                {
                    "detail": (
                        "Complaint not found or you do not "
                        "have permission to modify this feedback."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if complaint.status != Complaint.Status.RESOLVED:
            return Response(
                {
                    "detail": (
                        "Feedback can only be modified while "
                        "the complaint is resolved."
                    ),
                    "current_status": complaint.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        current_cycle = get_current_resolution_cycle(
            complaint
        )

        if feedback.resolution_cycle != current_cycle:
            return Response(
                {
                    "detail": (
                        "This feedback belongs to an earlier "
                        "resolution cycle and can no longer be "
                        "modified."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ComplaintResolutionFeedbackSerializer(
            feedback,
            data=request.data,
            partial=True,
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()

        return Response(
            {
                "detail": (
                    "Your resolution feedback has been "
                    "updated successfully."
                ),
                "feedback": serializer.data,
            },
            status=status.HTTP_200_OK,
        )