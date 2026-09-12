from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from organizations.models import Category
from organizations.serializers import CategorySerializer


class ActiveCategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        return (
            Category.objects
            .filter(
                is_active=True,
                department__is_active=True,
            )
            .select_related("department")
            .order_by(
                "department__name",
                "name",
            )
        )