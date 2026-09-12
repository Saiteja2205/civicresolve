from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated

from accounts.models import User
from accounts.permissions import IsAdminUserRole
from organizations.models import Category, Department
from organizations.serializers import (
    CategorySerializer,
    DepartmentSerializer,
)


class ActiveCategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        return (
            Category.objects
            .filter(
                is_active=True,
                department__is_active=True,
            )
            .select_related("department")
            .order_by(
                "department__name",
                "name",
            )
        )


class ActiveDepartmentListView(generics.ListAPIView):
    serializer_class = DepartmentSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        return Department.objects.filter(
            is_active=True,
        ).order_by("name")


class OfficerSerializer(serializers.Serializer):
    id = serializers.IntegerField(
        read_only=True,
    )
    email = serializers.EmailField(
        read_only=True,
    )
    phone = serializers.CharField(
        read_only=True,
    )
    department_id = serializers.IntegerField(
        read_only=True,
        allow_null=True,
    )
    department_name = serializers.CharField(
        read_only=True,
        allow_null=True,
    )
    is_active = serializers.BooleanField(
        read_only=True,
    )

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "email": instance.email,
            "phone": instance.phone,
            "department_id": instance.department_id,
            "department_name": (
                instance.department.name
                if instance.department
                else None
            ),
            "is_active": instance.is_active,
        }


class ActiveOfficerListView(generics.ListAPIView):
    serializer_class = OfficerSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminUserRole,
    ]

    def get_queryset(self):
        department_id = self.request.query_params.get(
            "department",
        )

        queryset = (
            User.objects
            .filter(
                role=User.Role.OFFICER,
                is_active=True,
                department__is_active=True,
            )
            .select_related("department")
            .order_by("email")
        )

        if department_id:
            queryset = queryset.filter(
                department_id=department_id,
            )

        return queryset