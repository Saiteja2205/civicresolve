from rest_framework import serializers

from .models import Complaint


class ComplaintSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    department_name = serializers.CharField(
        source="category.department.name",
        read_only=True,
    )

    class Meta:
        model = Complaint

        fields = [
            "id",
            "ticket_number",
            "user",
            "user_email",
            "category",
            "category_name",
            "department_name",
            "title",
            "description",
            "status",
            "priority",
            "location",
            "latitude",
            "longitude",
            "created_at",
            "updated_at",
            "resolved_at",
            "closed_at",
        ]

        read_only_fields = [
            "id",
            "ticket_number",
            "user",
            "user_email",
            "category_name",
            "department_name",
            "status",
            "created_at",
            "updated_at",
            "resolved_at",
            "closed_at",
        ]