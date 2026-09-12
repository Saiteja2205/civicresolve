from rest_framework import serializers

from organizations.models import Category, Department


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


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = [
            "id",
            "name",
            "description",
            "is_active",
        ]
        read_only_fields = [
            "id",
        ]


class OfficerSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    phone = serializers.CharField(read_only=True)
    department_id = serializers.IntegerField(
        read_only=True,
        allow_null=True,
    )
    department_name = serializers.CharField(
        read_only=True,
        allow_null=True,
    )
    is_active = serializers.BooleanField(
        read_only=True,
    )