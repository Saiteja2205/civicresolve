from django.conf import settings
from django.db import models
from pgvector.django import VectorField
from organizations.models import Category


class Complaint(models.Model):

    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        AI_ANALYZING = "AI_ANALYZING", "AI Analyzing"
        ASSIGNED = "ASSIGNED", "Assigned"
        ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        NEEDS_INFORMATION = "NEEDS_INFORMATION", "Needs Information"
        ESCALATED = "ESCALATED", "Escalated"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"
        REOPENED = "REOPENED", "Reopened"
        REJECTED = "REJECTED", "Rejected"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    ticket_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="complaints",
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="complaints",
    )

    title = models.CharField(max_length=200)

    description = models.TextField()

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    location = models.CharField(
        max_length=255,
        blank=True,
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    closed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = self.generate_ticket_number()

        super().save(*args, **kwargs)

    @staticmethod
    def generate_ticket_number():
        last_complaint = (
            Complaint.objects
            .order_by("-id")
            .first()
        )

        next_id = 1 if last_complaint is None else last_complaint.id + 1

        return f"CR-{next_id:06d}"

    def __str__(self):
        return f"{self.ticket_number} - {self.title}"


class ComplaintAnalysis(models.Model):

    complaint = models.OneToOneField(
        Complaint,
        on_delete=models.CASCADE,
        related_name="analysis",
    )

    summary = models.TextField(
        blank=True,
    )

    explanation = models.TextField(
        blank=True,
    )

    predicted_category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ai_predicted_complaints",
    )

    predicted_department = models.ForeignKey(
        "organizations.Department",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ai_predicted_complaints",
    )

    predicted_priority = models.CharField(
        max_length=20,
        choices=Complaint.Priority.choices,
        null=True,
        blank=True,
    )

    urgency_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    model_name = models.CharField(
        max_length=100,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"AI Analysis - {self.complaint.ticket_number}"


class ComplaintAssignment(models.Model):
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="assignments",
    )

    department = models.ForeignKey(
        "organizations.Department",
        on_delete=models.PROTECT,
        related_name="complaint_assignments",
    )

    officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="complaint_assignments",
    )

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assignments_created",
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    unassigned_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    reason = models.TextField(
        blank=True,
    )

    def __str__(self):
        return (
            f"{self.complaint.ticket_number} -> "
            f"{self.officer.email}"
        )


class ComplaintHistory(models.Model):
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="history",
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaint_history_changes",
    )

    old_status = models.CharField(
        max_length=30,
        choices=Complaint.Status.choices,
        blank=True,
    )

    new_status = models.CharField(
        max_length=30,
        choices=Complaint.Status.choices,
    )

    comment = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return (
            f"{self.complaint.ticket_number}: "
            f"{self.old_status or 'NEW'} -> {self.new_status}"
        )


class SLAPolicy(models.Model):
    priority = models.CharField(
        max_length=20,
        choices=Complaint.Priority.choices,
        unique=True,
    )

    response_time_hours = models.PositiveIntegerField()

    resolution_time_hours = models.PositiveIntegerField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["response_time_hours"]

    def __str__(self):
        return (
            f"{self.priority} - "
            f"{self.response_time_hours}h response / "
            f"{self.resolution_time_hours}h resolution"
        )


class ComplaintSLA(models.Model):
    complaint = models.OneToOneField(
        Complaint,
        on_delete=models.CASCADE,
        related_name="sla",
    )

    policy = models.ForeignKey(
        SLAPolicy,
        on_delete=models.PROTECT,
        related_name="complaint_slas",
    )

    response_deadline = models.DateTimeField()

    resolution_deadline = models.DateTimeField()

    response_completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    resolution_completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    response_breached = models.BooleanField(default=False)

    resolution_breached = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SLA - {self.complaint.ticket_number}"


class ComplaintEmbedding(models.Model):
    complaint = models.OneToOneField(
        Complaint,
        on_delete=models.CASCADE,
        related_name="embedding",
    )

    embedding = VectorField(
        dimensions=768,
    )

    embedding_model = models.CharField(
        max_length=100,
    )

    source_text_hash = models.CharField(
        max_length=64,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Embedding for {self.complaint.ticket_number}"


class ComplaintDuplicate(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Review"
        CONFIRMED = "CONFIRMED", "Confirmed Duplicate"
        REJECTED = "REJECTED", "Not a Duplicate"

    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="duplicate_candidates",
    )

    possible_duplicate = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="possible_duplicate_of",
    )

    similarity_score = models.DecimalField(
        max_digits=6,
        decimal_places=5,
    )

    detection_threshold = models.DecimalField(
        max_digits=6,
        decimal_places=5,
    )

    embedding_model = models.CharField(
        max_length=100,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    detected_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="duplicate_reviews",
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    review_comment = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = ["-detected_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["complaint", "possible_duplicate"],
                name="unique_complaint_duplicate_pair",
            ),
            models.CheckConstraint(
                condition=~models.Q(complaint=models.F("possible_duplicate")),
                name="complaint_duplicate_not_self",
            ),
        ]

        indexes = [
            models.Index(
                fields=["status", "-detected_at"],
                name="duplicate_status_detected_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.complaint.ticket_number} ~ "
            f"{self.possible_duplicate.ticket_number} "
            f"({self.similarity_score})"
        )

class ComplaintEvidence(models.Model):
    """
    Image evidence attached to a complaint.

    Each complaint can contain multiple evidence images.
    AI analysis is stored as structured metadata so the original
    evidence remains available independently of the AI result.
    """

    class EvidenceType(models.TextChoices):
        ROAD_DAMAGE = "ROAD_DAMAGE", "Road Damage"
        WATER_LEAKAGE = "WATER_LEAKAGE", "Water Leakage"
        GARBAGE = "GARBAGE", "Garbage / Waste"
        STREET_LIGHTING = "STREET_LIGHTING", "Street Lighting"
        ELECTRICITY = "ELECTRICITY", "Electricity"
        PUBLIC_SAFETY = "PUBLIC_SAFETY", "Public Safety"
        SANITATION = "SANITATION", "Sanitation"
        OTHER = "OTHER", "Other"

    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="evidence",
    )

    image = models.ImageField(
        upload_to="complaint-evidence/%Y/%m/%d/",
    )

    original_filename = models.CharField(
        max_length=255,
    )

    content_type = models.CharField(
        max_length=100,
    )

    file_size = models.PositiveIntegerField()

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_complaint_evidence",
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    # AI analysis fields

    analysis_completed = models.BooleanField(
        default=False,
    )

    evidence_type = models.CharField(
        max_length=30,
        choices=EvidenceType.choices,
        blank=True,
    )

    observations = models.TextField(
        blank=True,
    )

    severity_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    complaint_consistency = models.BooleanField(
        null=True,
        blank=True,
    )

    analysis_explanation = models.TextField(
        blank=True,
    )

    analysis_model = models.CharField(
        max_length=100,
        blank=True,
    )

    analyzed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return (
            f"Evidence for {self.complaint.ticket_number} - "
            f"{self.original_filename}"
        )