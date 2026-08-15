from django.contrib import admin

from .models import Complaint, ComplaintAssignment, ComplaintHistory


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        "ticket_number",
        "title",
        "user",
        "category",
        "status",
        "priority",
        "created_at",
    )

    list_filter = (
        "status",
        "priority",
        "category",
    )

    search_fields = (
        "ticket_number",
        "title",
        "description",
        "user__email",
    )

    readonly_fields = (
        "ticket_number",
        "created_at",
        "updated_at",
        "resolved_at",
        "closed_at",
    )
@admin.register(ComplaintAssignment)
class ComplaintAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "complaint",
        "department",
        "officer",
        "assigned_by",
        "assigned_at",
        "unassigned_at",
    )

    list_filter = (
        "department",
        "assigned_at",
    )

    search_fields = (
        "complaint__ticket_number",
        "officer__email",
        "assigned_by__email",
    )

    readonly_fields = (
        "assigned_at",
    )
@admin.register(ComplaintHistory)
class ComplaintHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "complaint",
        "old_status",
        "new_status",
        "changed_by",
        "created_at",
    )

    list_filter = (
        "old_status",
        "new_status",
        "created_at",
    )

    search_fields = (
        "complaint__ticket_number",
        "changed_by__email",
        "comment",
    )

    readonly_fields = (
        "created_at",
    )