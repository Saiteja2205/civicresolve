from django.db import transaction

from complaints.models import Complaint, ComplaintHistory


@transaction.atomic
def create_complaint(*, validated_data, created_by):
    """
    Creates a complaint and records its initial SUBMITTED history.
    """

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

    return complaint