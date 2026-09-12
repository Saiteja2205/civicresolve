from django.db import models, transaction
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from accounts.permissions import (
    IsAdminOrOfficer,
    IsAdminUserRole,
    IsCitizenUser,
    IsOfficerUserRole,
)

from .models import (
    Complaint,
    ComplaintAnalysis,
    ComplaintAssignment,
    ComplaintHistory,
    ComplaintSLA,
)

from .serializers import (
    ComplaintSerializer,
    ComplaintAnalysisSerializer,
    ComplaintAssignmentSerializer,
    ComplaintHistorySerializer,
    ComplaintSLASerializer,
)

from complaints.services.complaint_creation_service import (
    create_complaint,
)

from complaints.services.complaint_service import (
    change_complaint_status,
)

from organizations.models import Department


class ComplaintViewSet(viewsets.ModelViewSet):
    queryset = Complaint.objects.select_related(
        "user",
        "category",
        "category__department",
    ).all()

    serializer_class = ComplaintSerializer

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [
                IsAuthenticated,
                IsCitizenUser,
            ]

        elif self.action in [
            "update",
            "partial_update",
        ]:
            permission_classes = [
                IsAuthenticated,
                IsAdminOrOfficer,
            ]

        elif self.action == "destroy":
            permission_classes = [
                IsAuthenticated,
                IsAdminUserRole,
            ]

        elif self.action == "assign":
            permission_classes = [
                IsAuthenticated,
                IsAdminUserRole,
            ]

        elif self.action in [
            "acknowledge",
            "start",
            "resolve",
        ]:
            permission_classes = [
                IsAuthenticated,
                IsOfficerUserRole,
            ]

        elif self.action == "close":
            permission_classes = [
                IsAuthenticated,
                IsAdminUserRole,
            ]

        elif self.action == "history":
            permission_classes = [
                IsAuthenticated,
            ]

        else:
            permission_classes = [
                IsAuthenticated,
            ]

        return [
            permission()
            for permission in permission_classes
        ]

    def get_queryset(self):
        user = self.request.user

        if user.role == "ADMIN":
            return self.queryset

        if user.role == "OFFICER":
            return self.queryset.filter(
                assignments__officer=user,
                assignments__unassigned_at__isnull=True,
            ).distinct()

        return self.queryset.filter(
            user=user,
        )

    def perform_create(self, serializer):
        complaint = create_complaint(
            validated_data=serializer.validated_data,
            created_by=self.request.user,
        )

        serializer.instance = complaint

    @action(
        detail=True,
        methods=["post"],
    )
    @transaction.atomic
    def assign(self, request, pk=None):
        complaint = self.get_object()

        officer_id = request.data.get(
            "officer_id"
        )

        department_id = request.data.get(
            "department_id"
        )

        reason = request.data.get(
            "reason",
            "Complaint assigned to officer.",
        )

        if not officer_id:
            return Response(
                {
                    "detail": (
                        "officer_id is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not department_id:
            return Response(
                {
                    "detail": (
                        "department_id is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_assignment_statuses = {
            Complaint.Status.SUBMITTED,
            Complaint.Status.AI_ANALYZING,
            Complaint.Status.REOPENED,
            Complaint.Status.ASSIGNED,
        }

        if (
            complaint.status
            not in allowed_assignment_statuses
        ):
            return Response(
                {
                    "detail": (
                        "Only submitted, "
                        "AI-analyzing, reopened, "
                        "or assigned complaints "
                        "can be manually assigned."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            officer = (
                User.objects
                .select_related("department")
                .get(
                    id=officer_id,
                    role=User.Role.OFFICER,
                    is_active=True,
                )
            )

        except User.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Valid active officer "
                        "not found."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            department = Department.objects.get(
                id=department_id,
                is_active=True,
            )

        except Department.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Valid active department "
                        "not found."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            officer.department_id
            != department.id
        ):
            return Response(
                {
                    "detail": (
                        "Officer does not belong "
                        "to the selected department."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Close the currently active assignment.
        ComplaintAssignment.objects.filter(
            complaint=complaint,
            unassigned_at__isnull=True,
        ).update(
            unassigned_at=timezone.now()
        )

        assignment_reason = reason

        if (
            complaint.status
            == Complaint.Status.ASSIGNED
        ):
            assignment_reason = (
                "Complaint reassigned by "
                "administrator. "
                f"{reason}"
            )

        ComplaintAssignment.objects.create(
            complaint=complaint,
            department=department,
            officer=officer,
            assigned_by=request.user,
            reason=assignment_reason,
        )

        # A complaint that is already ASSIGNED
        # should remain ASSIGNED.
        #
        # For other valid assignment states,
        # move the complaint into ASSIGNED.
        if (
            complaint.status
            != Complaint.Status.ASSIGNED
        ):
            try:
                change_complaint_status(
                    complaint=complaint,
                    new_status=(
                        Complaint.Status.ASSIGNED
                    ),
                    changed_by=request.user,
                    comment=reason,
                )

            except ValueError as exc:
                return Response(
                    {
                        "detail": str(exc)
                    },
                    status=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                )

        return Response(
            {
                "detail": (
                    "Complaint reassigned "
                    "successfully."
                    if complaint.status
                    == Complaint.Status.ASSIGNED
                    and assignment_reason
                    != reason
                    else
                    "Complaint assigned "
                    "successfully."
                ),
                "complaint_id": complaint.id,
                "officer_id": officer.id,
                "department_id": department.id,
                "status": complaint.status,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
    )
    def acknowledge(
        self,
        request,
        pk=None,
    ):
        complaint = self.get_object()

        comment = request.data.get(
            "comment",
            "Complaint acknowledged by officer.",
        )

        try:
            change_complaint_status(
                complaint=complaint,
                new_status=(
                    Complaint.Status.ACKNOWLEDGED
                ),
                changed_by=request.user,
                comment=comment,
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": (
                    "Complaint acknowledged "
                    "successfully."
                ),
                "status": complaint.status,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
    )
    def start(
        self,
        request,
        pk=None,
    ):
        complaint = self.get_object()

        comment = request.data.get(
            "comment",
            "Complaint work started.",
        )

        try:
            change_complaint_status(
                complaint=complaint,
                new_status=(
                    Complaint.Status.IN_PROGRESS
                ),
                changed_by=request.user,
                comment=comment,
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": (
                    "Complaint marked as "
                    "in progress."
                ),
                "status": complaint.status,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
    )
    def resolve(
        self,
        request,
        pk=None,
    ):
        complaint = self.get_object()

        comment = request.data.get(
            "comment",
            "Complaint resolved by officer.",
        )

        try:
            change_complaint_status(
                complaint=complaint,
                new_status=(
                    Complaint.Status.RESOLVED
                ),
                changed_by=request.user,
                comment=comment,
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": (
                    "Complaint resolved "
                    "successfully."
                ),
                "status": complaint.status,
                "resolved_at": complaint.resolved_at,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
    )
    def close(
        self,
        request,
        pk=None,
    ):
        complaint = self.get_object()

        comment = request.data.get(
            "comment",
            "Complaint closed by administrator.",
        )

        try:
            change_complaint_status(
                complaint=complaint,
                new_status=(
                    Complaint.Status.CLOSED
                ),
                changed_by=request.user,
                comment=comment,
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": (
                    "Complaint closed "
                    "successfully."
                ),
                "status": complaint.status,
                "closed_at": complaint.closed_at,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def history(
        self,
        request,
        pk=None,
    ):
        complaint = self.get_object()

        history = (
            ComplaintHistory.objects
            .filter(
                complaint=complaint,
            )
            .select_related(
                "changed_by",
            )
            .order_by(
                "created_at",
            )
        )

        serializer = ComplaintHistorySerializer(
            history,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class ComplaintSLAViewSet(
    viewsets.ReadOnlyModelViewSet
):
    serializer_class = ComplaintSLASerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminUserRole,
    ]

    queryset = (
        ComplaintSLA.objects
        .select_related(
            "complaint",
            "policy",
        )
        .order_by(
            "-response_breached",
            "-resolution_breached",
            "resolution_deadline",
        )
    )

    def get_queryset(self):
        queryset = self.queryset

        status_filter = self.request.query_params.get(
            "status"
        )

        priority_filter = self.request.query_params.get(
            "priority"
        )

        breached_filter = self.request.query_params.get(
            "breached"
        )

        if status_filter:
            queryset = queryset.filter(
                complaint__status=status_filter
            )

        if priority_filter:
            queryset = queryset.filter(
                complaint__priority=priority_filter
            )

        if breached_filter == "true":
            queryset = queryset.filter(
                models.Q(
                    response_breached=True
                )
                | models.Q(
                    resolution_breached=True
                )
            )

        return queryset
class ComplaintAssignmentViewSet(
    viewsets.ModelViewSet
):
    queryset = (
        ComplaintAssignment.objects
        .select_related(
            "complaint",
            "department",
            "officer",
            "assigned_by",
        )
        .all()
    )

    serializer_class = (
        ComplaintAssignmentSerializer
    )

    def get_permissions(self):
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
        ]:
            permission_classes = [
                IsAuthenticated,
                IsAdminUserRole,
            ]

        else:
            permission_classes = [
                IsAuthenticated,
            ]

        return [
            permission()
            for permission in permission_classes
        ]

    def get_queryset(self):
        user = self.request.user

        if user.role == "ADMIN":
            queryset = self.queryset

        elif user.role == "OFFICER":
            queryset = self.queryset.filter(
                officer=user,
            )

        else:
            return self.queryset.none()

        complaint_id = (
            self.request.query_params.get(
                "complaint"
            )
        )

        if complaint_id:
            queryset = queryset.filter(
                complaint_id=complaint_id,
            )

        return queryset

    def perform_create(self, serializer):
        officer = (
            serializer.validated_data.get(
                "officer"
            )
        )

        department = (
            serializer.validated_data.get(
                "department"
            )
        )

        if officer is None:
            raise ValueError(
                "Officer is required."
            )

        if officer.role != "OFFICER":
            raise ValueError(
                "Selected user is not an officer."
            )

        if department is None:
            raise ValueError(
                "Department is required."
            )

        if (
            officer.department_id
            != department.id
        ):
            raise ValueError(
                "Officer does not belong "
                "to the selected department."
            )

        serializer.save(
            assigned_by=self.request.user
        )