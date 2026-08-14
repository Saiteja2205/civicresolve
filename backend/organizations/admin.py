from django.contrib import admin

from .models import Category, Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "is_active", "created_at")
    list_filter = ("department", "is_active")
    search_fields = ("name", "department__name")