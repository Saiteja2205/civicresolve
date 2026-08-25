from django.utils import timezone

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import (
    IsAdminOrOfficer,
    IsAdminUserRole,
    IsCitizenUser,
    IsOfficerUserRole,
)

from .models import Complaint
from .serializers import ComplaintSerializer


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

        elif self.action in ["update", "partial_update"]:
            permission_classes = [
                IsAdminOrOfficer,
            ]

        elif self.action == "destroy":
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
                assignments__officer=user
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

        serializer = self.get_serializer(complaint)

        return Response(serializer.data)

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
                    "detail": "Only submitted complaints can be assigned."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        complaint.status = "ASSIGNED"
        complaint.save()

        return Response(
            {
                "message": "Complaint assigned successfully.",
                "status": complaint.status,
            }
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsOfficerUserRole],
    )
    def acknowledge(self, request, pk=None):

        complaint = self.get_object()

        if complaint.status != "ASSIGNED":
            return Response(
                {
                    "detail": "Only assigned complaints can be acknowledged."
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
    def start(self, request, pk=None):

        complaint = self.get_object()

        if complaint.status != "ACKNOWLEDGED":
            return Response(
                {
                    "detail": (
                        "Complaint must be acknowledged "
                        "before work can begin."
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
    def resolve(self, request, pk=None):

        complaint = self.get_object()

        if complaint.status != "IN_PROGRESS":
            return Response(
                {
                    "detail": (
                        "Only complaints in progress "
                        "can be resolved."
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
    def close(self, request, pk=None):

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