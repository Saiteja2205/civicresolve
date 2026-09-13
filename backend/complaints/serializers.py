from rest_framework import serializers

from .models import (
    Complaint,
    ComplaintAnalysis,
    ComplaintAssignment,
    ComplaintDuplicate,
    ComplaintHistory,
    ComplaintSLA,
)


class ComplaintAnalysisSerializer(
    serializers.ModelSerializer
):
    complaint_ticket_number = serializers.CharField(
        source="complaint.ticket_number",
        read_only=True,
    )

    predicted_category_name = serializers.CharField(
        source="predicted_category.name",
        read_only=True,
    )

    predicted_department_name = serializers.CharField(
        source="predicted_department.name",
        read_only=True,
    )

    class Meta:
        model = ComplaintAnalysis
        fields = [
            "id",
            "complaint",
            "complaint_ticket_number",
            "summary",
            "explanation",
            "predicted_category",
            "predicted_category_name",
            "predicted_department",
            "predicted_department_name",
            "predicted_priority",
            "urgency_score",
            "confidence_score",
            "model_name",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "complaint",
            "complaint_ticket_number",
            "summary",
            "explanation",
            "predicted_category",
            "predicted_category_name",
            "predicted_department",
            "predicted_department_name",
            "predicted_priority",
            "urgency_score",
            "confidence_score",
            "model_name",
            "created_at",
            "updated_at",
        ]


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

    ai_analysis = ComplaintAnalysisSerializer(
        source="analysis",
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
            "ai_analysis",
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
            "ai_analysis",
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
            "officer_email",
            "department_name",
        ]


class ComplaintSLASerializer(serializers.ModelSerializer):
    complaint_ticket_number = serializers.CharField(
        source="complaint.ticket_number",
        read_only=True,
    )

    priority = serializers.CharField(
        source="complaint.priority",
        read_only=True,
    )

    status = serializers.CharField(
        source="complaint.status",
        read_only=True,
    )

    title = serializers.CharField(
        source="complaint.title",
        read_only=True,
    )

    policy_priority = serializers.CharField(
        source="policy.priority",
        read_only=True,
    )

    response_time_hours = serializers.IntegerField(
        source="policy.response_time_hours",
        read_only=True,
    )

    resolution_time_hours = serializers.IntegerField(
        source="policy.resolution_time_hours",
        read_only=True,
    )

    class Meta:
        model = ComplaintSLA

        fields = [
            "id",
            "complaint",
            "complaint_ticket_number",
            "title",
            "priority",
            "status",
            "policy",
            "policy_priority",
            "response_time_hours",
            "resolution_time_hours",
            "response_deadline",
            "resolution_deadline",
            "response_completed_at",
            "resolution_completed_at",
            "response_breached",
            "resolution_breached",
        ]

        read_only_fields = fields


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
            "changed_by",
            "changed_by_email",
            "old_status",
            "new_status",
            "comment",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "changed_by",
            "changed_by_email",
            "old_status",
            "new_status",
            "created_at",
        ]


class ComplaintDuplicateSerializer(
    serializers.ModelSerializer
):
    complaint_ticket_number = serializers.CharField(
        source="complaint.ticket_number",
        read_only=True,
    )

    complaint_title = serializers.CharField(
        source="complaint.title",
        read_only=True,
    )

    possible_duplicate_ticket_number = serializers.CharField(
        source="possible_duplicate.ticket_number",
        read_only=True,
    )

    possible_duplicate_title = serializers.CharField(
        source="possible_duplicate.title",
        read_only=True,
    )

    possible_duplicate_status = serializers.CharField(
        source="possible_duplicate.status",
        read_only=True,
    )

    possible_duplicate_priority = serializers.CharField(
        source="possible_duplicate.priority",
        read_only=True,
    )

    reviewed_by_email = serializers.EmailField(
        source="reviewed_by.email",
        read_only=True,
    )

    similarity_percentage = serializers.SerializerMethodField()

    class Meta:
        model = ComplaintDuplicate

        fields = [
            "id",
            "complaint",
            "complaint_ticket_number",
            "complaint_title",
            "possible_duplicate",
            "possible_duplicate_ticket_number",
            "possible_duplicate_title",
            "possible_duplicate_status",
            "possible_duplicate_priority",
            "similarity_score",
            "similarity_percentage",
            "detection_threshold",
            "embedding_model",
            "status",
            "detected_at",
            "updated_at",
            "reviewed_by",
            "reviewed_by_email",
            "reviewed_at",
            "review_comment",
        ]

        read_only_fields = [
            "id",
            "complaint",
            "complaint_ticket_number",
            "complaint_title",
            "possible_duplicate",
            "possible_duplicate_ticket_number",
            "possible_duplicate_title",
            "possible_duplicate_status",
            "possible_duplicate_priority",
            "similarity_score",
            "similarity_percentage",
            "detection_threshold",
            "embedding_model",
            "status",
            "detected_at",
            "updated_at",
            "reviewed_by",
            "reviewed_by_email",
            "reviewed_at",
        ]

    def get_similarity_percentage(self, obj):
        return round(float(obj.similarity_score) * 100, 2)