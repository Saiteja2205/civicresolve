from rest_framework import viewsets

from .models import Complaint
from .serializers import ComplaintSerializer


class ComplaintViewSet(viewsets.ModelViewSet):
    queryset = Complaint.objects.select_related(
        "user",
        "category",
        "category__department",
    ).all()

    serializer_class = ComplaintSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

