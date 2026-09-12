from rest_framework import serializers

from organizations.models import Category


class CategorySerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(
        source="department.name",
        read_only=True,
    )

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "description",
            "department",
            "department_name",
        ]
        read_only_fields = [
            "id",
            "department_name",
        ]