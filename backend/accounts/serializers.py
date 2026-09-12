from rest_framework import serializers

from .models import User


class CurrentUserSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(
        source="department.name",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = User

        fields = [
            "id",
            "email",
            "phone",
            "role",
            "department",
            "department_name",
        ]

        read_only_fields = [
            "id",
            "email",
            "phone",
            "role",
            "department",
            "department_name",
        ]