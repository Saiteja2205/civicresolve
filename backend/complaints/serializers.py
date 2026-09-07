from rest_framework import serializers

from .models import (
    Complaint,
    ComplaintAssignment,
    ComplaintHistory,
)


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
            "priority",
            "created_at",
            "updated_at",
            "resolved_at",
            "closed_at",
        ]

    def validate_title(self, value):

        value = value.strip()

        if len(value) < 5:
            raise serializers.ValidationError(
                "Title must contain at least 5 characters."
            )

        if len(value) > 200:
            raise serializers.ValidationError(
                "Title cannot exceed 200 characters."
            )

        return value

    def validate_description(self, value):

        value = value.strip()

        if len(value) < 10:
            raise serializers.ValidationError(
                "Description must contain at least 10 characters."
            )

        return value

    def validate_location(self, value):

        if not value:
            return value

        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "Location is too short."
            )

        return value

    def validate_latitude(self, value):

        if value is None:
            return value

        if value < -90 or value > 90:
            raise serializers.ValidationError(
                "Latitude must be between -90 and 90."
            )

        return value

    def validate_longitude(self, value):

        if value is None:
            return value

        if value < -180 or value > 180:
            raise serializers.ValidationError(
                "Longitude must be between -180 and 180."
            )

        return value


class ComplaintAssignmentSerializer(
    serializers.ModelSerializer
):

    officer_email = serializers.EmailField(
        source="officer.email",
        read_only=True,
    )

    department_name = serializers.CharField(
        source="department.name",
        read_only=True,
    )

    assigned_by_email = serializers.EmailField(
        source="assigned_by.email",
        read_only=True,
    )

    class Meta:
        model = ComplaintAssignment

        fields = [
            "id",
            "complaint",
            "department",
            "department_name",
            "officer",
            "officer_email",
            "assigned_by",
            "assigned_by_email",
            "assigned_at",
            "unassigned_at",
            "reason",
        ]

        read_only_fields = [
            "id",
            "assigned_by",
            "assigned_by_email",
            "assigned_at",
            "unassigned_at",
            "department_name",
            "officer_email",
        ]


class ComplaintHistorySerializer(
    serializers.ModelSerializer
):

    changed_by_email = serializers.EmailField(
        source="changed_by.email",
        read_only=True,
    )

    class Meta:
        model = ComplaintHistory

        fields = [
            "id",
            "complaint",
            "old_status",
            "new_status",
            "changed_by",
            "changed_by_email",
            "comment",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "complaint",
            "old_status",
            "new_status",
            "changed_by",
            "changed_by_email",
            "comment",
            "created_at",
        ]