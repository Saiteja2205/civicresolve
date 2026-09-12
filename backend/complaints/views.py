from django.db import transaction
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
from complaints.models import (
    Complaint,
    ComplaintAssignment,
    ComplaintHistory,
)
from complaints.serializers import (
    ComplaintAssignmentSerializer,
    ComplaintHistorySerializer,
    ComplaintSerializer,
)
from complaints.services.complaint_creation_service import create_complaint
from complaints.services.complaint_service import change_complaint_status
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
            permission_classes = [IsAuthenticated, IsCitizenUser]

        elif self.action in ["update", "partial_update"]:
            permission_classes = [IsAuthenticated, IsAdminOrOfficer]

        elif self.action == "destroy":
            permission_classes = [IsAuthenticated, IsAdminUserRole]

        elif self.action == "assign":
            permission_classes = [IsAuthenticated, IsAdminUserRole]

        elif self.action in ["acknowledge", "start", "resolve"]:
            permission_classes = [IsAuthenticated, IsOfficerUserRole]

        elif self.action == "close":
            permission_classes = [IsAuthenticated, IsAdminUserRole]

        elif self.action == "history":
            permission_classes = [IsAuthenticated]

        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user

        if user.role == "ADMIN":
            return self.queryset

        if user.role == "OFFICER":
            return self.queryset.filter(
                assignments__officer=user,
                assignments__unassigned_at__isnull=True,
            ).distinct()

        return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        complaint = create_complaint(
            validated_data=serializer.validated_data,
            created_by=self.request.user,
        )

        serializer.instance = complaint

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def assign(self, request, pk=None):
        complaint = self.get_object()

        officer_id = request.data.get("officer_id")
        department_id = request.data.get("department_id")
        reason = request.data.get(
            "reason",
            "Complaint assigned to officer.",
        )

        if not officer_id:
            return Response(
                {"detail": "officer_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not department_id:
            return Response(
                {"detail": "department_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            officer = User.objects.get(
                id=officer_id,
                role="OFFICER",
            )
        except User.DoesNotExist:
            return Response(
                {"detail": "Valid officer not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            department = Department.objects.get(id=department_id)
        except Department.DoesNotExist:
            return Response(
                {"detail": "Valid department not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if officer.department_id != department.id:
            return Response(
                {
                    "detail": (
                        "Officer does not belong to the selected department."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        ComplaintAssignment.objects.filter(
            complaint=complaint,
            unassigned_at__isnull=True,
        ).update(
            unassigned_at=timezone.now()
        )

        ComplaintAssignment.objects.create(
            complaint=complaint,
            department=department,
            officer=officer,
            assigned_by=request.user,
            reason=reason,
        )

        try:
            change_complaint_status(
                complaint=complaint,
                new_status=Complaint.Status.ASSIGNED,
                changed_by=request.user,
                comment=reason,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Complaint assigned successfully.",
                "complaint_id": complaint.id,
                "officer_id": officer.id,
                "department_id": department.id,
                "status": complaint.status,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        complaint = self.get_object()

        comment = request.data.get(
            "comment",
            "Complaint acknowledged by officer.",
        )

        try:
            change_complaint_status(
                complaint=complaint,
                new_status=Complaint.Status.ACKNOWLEDGED,
                changed_by=request.user,
                comment=comment,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Complaint acknowledged successfully.",
                "status": complaint.status,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        complaint = self.get_object()

        comment = request.data.get(
            "comment",
            "Complaint work started.",
        )

        try:
            change_complaint_status(
                complaint=complaint,
                new_status=Complaint.Status.IN_PROGRESS,
                changed_by=request.user,
                comment=comment,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Complaint marked as in progress.",
                "status": complaint.status,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        complaint = self.get_object()

        comment = request.data.get(
            "comment",
            "Complaint resolved by officer.",
        )

        try:
            change_complaint_status(
                complaint=complaint,
                new_status=Complaint.Status.RESOLVED,
                changed_by=request.user,
                comment=comment,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Complaint resolved successfully.",
                "status": complaint.status,
                "resolved_at": complaint.resolved_at,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        complaint = self.get_object()

        comment = request.data.get(
            "comment",
            "Complaint closed by administrator.",
        )

        try:
            change_complaint_status(
                complaint=complaint,
                new_status=Complaint.Status.CLOSED,
                changed_by=request.user,
                comment=comment,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Complaint closed successfully.",
                "status": complaint.status,
                "closed_at": complaint.closed_at,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
    )
    def history(self, request, pk=None):
        complaint = self.get_object()

        history = ComplaintHistory.objects.filter(
            complaint=complaint
        ).select_related(
            "changed_by"
        ).order_by(
            "created_at"
        )

        serializer = ComplaintHistorySerializer(
            history,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class ComplaintAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ComplaintAssignment.objects.select_related(
        "complaint",
        "department",
        "officer",
        "assigned_by",
    ).all()

    serializer_class = ComplaintAssignmentSerializer

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

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user

        if user.role == "ADMIN":
            return self.queryset

        if user.role == "OFFICER":
            return self.queryset.filter(
                officer=user
            )

        return self.queryset.none()

    def perform_create(self, serializer):
        officer = serializer.validated_data.get("officer")
        department = serializer.validated_data.get("department")

        if officer is None:
            raise ValueError("Officer is required.")

        if officer.role != "OFFICER":
            raise ValueError(
                "Selected user is not an officer."
            )

        if department is None:
            raise ValueError("Department is required.")

        if officer.department_id != department.id:
            raise ValueError(
                "Officer does not belong to the selected department."
            )

        serializer.save(
            assigned_by=self.request.user
        )