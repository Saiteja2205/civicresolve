from rest_framework import permissions, viewsets

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