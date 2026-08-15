from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    ordering = ("email",)
    list_display = (
        "email",
        "role",
        "department",
        "is_active",
        "is_staff",
    )
    list_filter = (
        "role",
        "department",
        "is_active",
        "is_staff",
    )
    search_fields = (
        "email",
        "phone",
        "department__name",
    )

    fieldsets = (
        (None, {
            "fields": ("email", "password"),
        }),
        ("Personal Information", {
            "fields": ("first_name", "last_name", "phone"),
        }),
        ("Organization", {
            "fields": ("role", "department"),
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
        }),
        ("Important Dates", {
            "fields": (
                "last_login",
                "date_joined",
            ),
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "password1",
                "password2",
                "phone",
                "role",
                "department",
                "is_active",
                "is_staff",
            ),
        }),
    )

    readonly_fields = (
        "last_login",
        "date_joined",
    )