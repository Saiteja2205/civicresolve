from django.urls import path
from rest_framework.routers import DefaultRouter

from .resolution_assistant_views import (
    ComplaintResolutionAssistantView,
)
from .resolution_views import ComplaintReopenView
from .sla_risk_views import ComplaintSLARiskView
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
        "complaints/<int:complaint_id>/reopen/",
        ComplaintReopenView.as_view(),
        name="complaint-reopen",
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
        "activity/",
        UserActivityListView.as_view(),
        name="user-activity",
    ),
]

urlpatterns += router.urls