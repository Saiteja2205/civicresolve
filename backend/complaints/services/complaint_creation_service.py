from django.db import transaction

from complaints.models import Complaint, ComplaintHistory
from complaints.services.ai_orchestration_service import run_ai_analysis
from complaints.services.assignment_service import assign_complaint
from complaints.services.sla_service import create_complaint_sla


@transaction.atomic
def create_complaint(*, validated_data, created_by):
    complaint = Complaint.objects.create(
        **validated_data,
        user=created_by,
        status=Complaint.Status.SUBMITTED,
    )

    ComplaintHistory.objects.create(
        complaint=complaint,
        changed_by=created_by,
        old_status="",
        new_status=complaint.status,
        comment="Complaint submitted.",
    )

    # Run AI analysis first.
    # The AI service moves the complaint to AI_ANALYZING
    # while processing and returns success/failure information.
    ai_result = run_ai_analysis(complaint)

    complaint.refresh_from_db()

    # If AI analysis failed, do not attempt automatic assignment.
    # The complaint remains safely in SUBMITTED status instead
    # of causing a server error.
    if not ai_result.get("success"):
        return complaint

    # AI analysis succeeded, so the complaint should now be
    # in AI_ANALYZING status and can proceed to routing/assignment.
    assign_complaint(complaint)

    complaint.refresh_from_db()

    # SLA is created only after successful assignment.
    create_complaint_sla(complaint)

    complaint.refresh_from_db()

    return complaint