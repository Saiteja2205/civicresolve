from django.db import transaction

from complaints.models import Complaint, ComplaintHistory
from complaints.services.ai_orchestration_service import run_ai_analysis
from complaints.services.assignment_service import assign_complaint
from complaints.services.sla_service import create_complaint_sla


@transaction.atomic
def create_complaint(*, validated_data, created_by):
    """
    Create a complaint and run the initial CivicResolve
    processing workflow.

    Workflow:

    1. Create complaint.
    2. Record submission history.
    3. Run AI analysis.
    4. Automatically assign an officer.
    5. Create the complaint SLA.
    6. Return the fully processed complaint.
    """

    complaint = Complaint.objects.create(
        **validated_data,
        user=created_by,
        status=Complaint.Status.AI_ANALYZING,
    )

    ComplaintHistory.objects.create(
        complaint=complaint,
        changed_by=created_by,
        old_status="",
        new_status=complaint.status,
        comment="Complaint submitted and AI analysis started.",
    )

    run_ai_analysis(complaint)

    complaint.refresh_from_db()

    assign_complaint(complaint)

    complaint.refresh_from_db()

    create_complaint_sla(complaint)

    complaint.refresh_from_db()

    return complaint