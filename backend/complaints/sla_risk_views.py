from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from complaints.models import Complaint
from complaints.services.sla_risk_service import (
    SLARiskError,
    calculate_sla_risk,
)


class ComplaintSLARiskView(APIView):
    """
    Return the current predictive SLA risk for a complaint.

    Citizens can access their own complaints.
    Officers can access complaints currently assigned to them.
    Administrators can access all complaints.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def get_complaint(self, request, complaint_id):
        queryset = (
            Complaint.objects
            .select_related(
                "category",
                "category__department",
                "analysis",
            )
            .prefetch_related(
                "assignments",
                "history",
            )
        )

        if request.user.role == User.Role.ADMIN:
            return get_object_or_404(
                queryset,
                id=complaint_id,
            )

        if request.user.role == User.Role.OFFICER:
            return get_object_or_404(
                queryset.filter(
                    assignments__officer=request.user,
                    assignments__unassigned_at__isnull=True,
                ).distinct(),
                id=complaint_id,
            )

        return get_object_or_404(
            queryset,
            id=complaint_id,
            user=request.user,
        )

    def get(
        self,
        request,
        complaint_id,
    ):
        complaint = self.get_complaint(
            request,
            complaint_id,
        )

        try:
            risk = calculate_sla_risk(
                complaint
            )

        except SLARiskError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=400,
            )

        return Response(
            risk,
            status=200,
        )