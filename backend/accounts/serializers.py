from rest_framework import serializers

from .models import User


class CurrentUserSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(
        source="department.name",
        read_only=True,
    )

    role_display = serializers.CharField(
        source="get_role_display",
        read_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "phone",
            "role",
            "role_display",
            "department",
            "department_name",
            "first_name",
            "last_name",
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(
        source="department.name",
        read_only=True,
    )

    role_display = serializers.CharField(
        source="get_role_display",
        read_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "phone",
            "role",
            "role_display",
            "department",
            "department_name",
            "first_name",
            "last_name",
        ]

        read_only_fields = [
            "id",
            "email",
            "role",
            "role_display",
            "department",
            "department_name",
        ]

    def validate_phone(self, value):
        value = value.strip()

        if value and not value.isdigit():
            raise serializers.ValidationError(
                "Phone number must contain only digits."
            )

        if value and len(value) < 10:
            raise serializers.ValidationError(
                "Phone number must contain at least 10 digits."
            )

        if value and len(value) > 15:
            raise serializers.ValidationError(
                "Phone number cannot exceed 15 digits."
            )

        return value