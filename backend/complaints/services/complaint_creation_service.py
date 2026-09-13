from django.db import transaction

from complaints.models import Complaint, ComplaintDuplicate, ComplaintHistory
from complaints.services.ai_orchestration_service import run_ai_analysis
from complaints.services.assignment_service import assign_complaint
from complaints.services.duplicate_detection_service import (
    DuplicateDetectionError,
    SemanticDuplicateDetector,
)
from complaints.services.sla_service import create_complaint_sla


def persist_duplicate_candidates(*, complaint, duplicate_results, detector):
    """
    Persist semantic duplicate candidates for a complaint.

    Existing review decisions are preserved. If a candidate was previously
    rejected or confirmed, a new detection pass does not overwrite that
    human decision.
    """
    for result in duplicate_results:
        possible_duplicate = result["complaint"]

        ComplaintDuplicate.objects.get_or_create(
            complaint=complaint,
            possible_duplicate=possible_duplicate,
            defaults={
                "similarity_score": result["similarity_score"],
                "detection_threshold": detector.similarity_threshold,
                "embedding_model": (
                    complaint.embedding.embedding_model
                ),
                "status": ComplaintDuplicate.Status.PENDING,
            },
        )


def detect_and_persist_duplicates(complaint):
    """
    Detect semantically similar complaints and persist the results.

    Duplicate detection is a non-critical enhancement. Any detection
    failure is converted into a safe result so complaint creation itself
    is never blocked.
    """
    detector = SemanticDuplicateDetector()

    try:
        duplicate_results = detector.find_similar_complaints(complaint)
    except DuplicateDetectionError:
        return []

    persist_duplicate_candidates(
        complaint=complaint,
        duplicate_results=duplicate_results,
        detector=detector,
    )

    return duplicate_results


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

    # AI analysis succeeded, so the complaint can proceed
    # to routing and automatic officer assignment.
    assign_complaint(complaint)

    complaint.refresh_from_db()

    # SLA is created only after successful assignment.
    create_complaint_sla(complaint)

    complaint.refresh_from_db()

    # Semantic duplicate detection is a non-blocking enhancement.
    # A failure here must never prevent successful complaint creation.
    detect_and_persist_duplicates(complaint)

    complaint.refresh_from_db()

    return complaint