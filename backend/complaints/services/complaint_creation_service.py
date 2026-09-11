from django.db import transaction

from complaints.models import Complaint, ComplaintHistory
from complaints.services.ai_orchestration_service import (
    run_ai_analysis,
)


@transaction.atomic
def create_complaint(*, validated_data, created_by):
    complaint = Complaint.objects.create(
        **validated_data,
        user=created_by,
    )

    ComplaintHistory.objects.create(
        complaint=complaint,
        changed_by=created_by,
        old_status="",
        new_status=complaint.status,
        comment="Complaint submitted.",
    )

    run_ai_analysis(
        complaint
    )

    complaint.refresh_from_db()

    return complaint