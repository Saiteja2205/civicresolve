from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .ai_evaluation_views import AIEvaluationView
from .resolution_assistant_views import (
    ComplaintResolutionAssistantView,
)
from .resolution_feedback_views import (
    ComplaintResolutionFeedbackDetailView,
    ComplaintResolutionFeedbackView,
)
from .resolution_views import (
    ComplaintReopenView,
)
from .sla_risk_views import (
    ComplaintSLARiskView,
)
from .voice_translation_views import (
    VoiceComplaintTranslationView,
)
from .views import (
    ComplaintAssignmentViewSet,
    ComplaintDuplicateViewSet,
    ComplaintEvidenceViewSet,
    ComplaintSLAViewSet,
    ComplaintViewSet,
    UserActivityListView,
)


router = DefaultRouter()


router.register(
    r"complaints",
    ComplaintViewSet,
    basename="complaint",
)


router.register(
    r"assignments",
    ComplaintAssignmentViewSet,
    basename="assignment",
)


router.register(
    r"sla",
    ComplaintSLAViewSet,
    basename="sla",
)


router.register(
    r"complaint-duplicates",
    ComplaintDuplicateViewSet,
    basename="complaint-duplicate",
)


router.register(
    r"complaint-evidence",
    ComplaintEvidenceViewSet,
    basename="complaint-evidence",
)


urlpatterns = [
    path(
        "",
        include(router.urls),
    ),

    path(
        "complaints/<int:complaint_id>/reopen/",
        ComplaintReopenView.as_view(),
        name="complaint-reopen",
    ),

    path(
        "complaints/<int:complaint_id>/resolution-feedback/",
        ComplaintResolutionFeedbackView.as_view(),
        name="complaint-resolution-feedback",
    ),

    path(
        "complaints/resolution-feedback/<int:feedback_id>/",
        ComplaintResolutionFeedbackDetailView.as_view(),
        name="complaint-resolution-feedback-detail",
    ),

    path(
        "complaints/<int:complaint_id>/sla-risk/",
        ComplaintSLARiskView.as_view(),
        name="complaint-sla-risk",
    ),

    path(
        "complaints/<int:complaint_id>/resolution-assistant/",
        ComplaintResolutionAssistantView.as_view(),
        name="complaint-resolution-assistant",
    ),

    path(
        "ai-evaluation/",
        AIEvaluationView.as_view(),
        name="ai-evaluation",
    ),

    path(
        "activity/",
        UserActivityListView.as_view(),
        name="user-activity",
    ),
    path(
        "voice-translation/",
        VoiceComplaintTranslationView.as_view(),
        name="voice-complaint-translation",
    ),
]