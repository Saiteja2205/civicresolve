from django.utils import timezone

from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from accounts.permissions import (
    IsAdminOrOfficer,
    IsAdminUserRole,
    IsCitizenUser,
    IsOfficerUserRole,
)
from organizations.models import Department

from .models import Complaint, ComplaintAssignment
from .serializers import (
    ComplaintAssignmentSerializer,
    ComplaintSerializer,
)


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
                IsCitizenUser,
            ]

        elif self.action in [
            "update",
            "partial_update",
        ]:
            permission_classes = [
                IsAdminOrOfficer,
            ]

        elif self.action == "destroy":
            permission_classes = [
                IsAdminUserRole,
            ]

        elif self.action == "assign":
            permission_classes = [
                IsAdminUserRole,
            ]

        elif self.action in [
            "acknowledge",
            "start",
            "resolve",
        ]:
            permission_classes = [
                IsOfficerUserRole,
            ]

        elif self.action == "close":
            permission_classes = [
                IsAdminUserRole,
            ]

        else:
            permission_classes = [
                permissions.IsAuthenticated,
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
            user=user
        )

    def perform_create(self, serializer):

        serializer.save(
            user=self.request.user
        )

    def change_status(self, complaint, new_status):

        complaint.status = new_status

        if new_status == "RESOLVED":
            complaint.resolved_at = timezone.now()

        if new_status == "CLOSED":
            complaint.closed_at = timezone.now()

        complaint.save()

        serializer = self.get_serializer(
            complaint
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdminUserRole],
    )
    def assign(self, request, pk=None):

        complaint = self.get_object()

        if complaint.status != "SUBMITTED":
            return Response(
                {
                    "detail": (
                        "Only submitted complaints "
                        "can be assigned."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        officer_id = request.data.get(
            "officer"
        )

        department_id = request.data.get(
            "department"
        )

        reason = request.data.get(
            "reason",
            "",
        )

        if not officer_id:
            return Response(
                {
                    "officer": (
                        "This field is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not department_id:
            return Response(
                {
                    "department": (
                        "This field is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            officer = User.objects.get(
                id=officer_id
            )

        except User.DoesNotExist:
            return Response(
                {
                    "officer": "Officer not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            department = Department.objects.get(
                id=department_id
            )

        except Department.DoesNotExist:
            return Response(
                {
                    "department": (
                        "Department not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if officer.role != "OFFICER":
            return Response(
                {
                    "officer": (
                        "Selected user is not "
                        "an officer."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if officer.department_id != department.id:
            return Response(
                {
                    "officer": (
                        "Officer does not belong "
                        "to the selected department."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        active_assignment = (
            ComplaintAssignment.objects
            .filter(
                complaint=complaint,
                unassigned_at__isnull=True,
            )
            .first()
        )

        if active_assignment:
            active_assignment.unassigned_at = (
                timezone.now()
            )

            active_assignment.save(
                update_fields=[
                    "unassigned_at"
                ]
            )

        assignment = (
            ComplaintAssignment.objects.create(
                complaint=complaint,
                department=department,
                officer=officer,
                assigned_by=request.user,
                reason=reason,
            )
        )

        complaint.status = "ASSIGNED"

        complaint.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return Response(
            {
                "message": (
                    "Complaint assigned "
                    "successfully."
                ),
                "complaint": (
                    complaint.ticket_number
                ),
                "assignment_id": assignment.id,
                "officer": officer.email,
                "department": department.name,
                "status": complaint.status,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsOfficerUserRole],
    )
    def acknowledge(
        self,
        request,
        pk=None,
    ):

        complaint = self.get_object()

        if complaint.status != "ASSIGNED":
            return Response(
                {
                    "detail": (
                        "Only assigned complaints "
                        "can be acknowledged."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return self.change_status(
            complaint,
            "ACKNOWLEDGED",
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsOfficerUserRole],
    )
    def start(
        self,
        request,
        pk=None,
    ):

        complaint = self.get_object()

        if complaint.status != "ACKNOWLEDGED":
            return Response(
                {
                    "detail": (
                        "Complaint must be "
                        "acknowledged before "
                        "work can begin."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return self.change_status(
            complaint,
            "IN_PROGRESS",
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsOfficerUserRole],
    )
    def resolve(
        self,
        request,
        pk=None,
    ):

        complaint = self.get_object()

        if complaint.status != "IN_PROGRESS":
            return Response(
                {
                    "detail": (
                        "Only complaints in "
                        "progress can be resolved."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return self.change_status(
            complaint,
            "RESOLVED",
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdminUserRole],
    )
    def close(
        self,
        request,
        pk=None,
    ):

        complaint = self.get_object()

        if complaint.status != "RESOLVED":
            return Response(
                {
                    "detail": (
                        "Only resolved complaints "
                        "can be closed."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return self.change_status(
            complaint,
            "CLOSED",
        )


class ComplaintAssignmentViewSet(
    viewsets.ModelViewSet
):

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
                IsAdminUserRole,
            ]

        else:
            permission_classes = [
                IsAdminOrOfficer,
            ]

        return [
            permission()
            for permission in permission_classes
        ]

    def get_queryset(self):

        user = self.request.user

        if user.role == "ADMIN":
            return self.queryset

        return self.queryset.filter(
            officer=user
        )

    def perform_create(self, serializer):

        complaint = serializer.validated_data[
            "complaint"
        ]

        officer = serializer.validated_data[
            "officer"
        ]

        department = serializer.validated_data[
            "department"
        ]

        if officer.role != "OFFICER":
            raise serializers.ValidationError(
                {
                    "officer": (
                        "Selected user is not "
                        "an officer."
                    )
                }
            )

        if officer.department_id != department.id:
            raise serializers.ValidationError(
                {
                    "officer": (
                        "Officer does not belong "
                        "to the selected department."
                    )
                }
            )

        serializer.save(
            assigned_by=self.request.user
        )