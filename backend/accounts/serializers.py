from django.contrib.auth.password_validation import validate_password
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


class CitizenRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    password_confirm = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "phone",
            "password",
            "password_confirm",
        ]

    def validate_email(self, value):
        value = value.strip().lower()

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        return value

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

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError(
                {
                    "password_confirm": "Passwords do not match."
                }
            )

        validate_password(password)

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")

        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            role=User.Role.USER,
            **validated_data,
        )

        return user