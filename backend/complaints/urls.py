from django.urls import path
from rest_framework.routers import DefaultRouter

from .resolution_views import ComplaintReopenView
from .views import (
    ComplaintAssignmentViewSet,
    ComplaintSLAViewSet,
    ComplaintViewSet,
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


urlpatterns = [
    path(
        "complaints/<int:complaint_id>/reopen/",
        ComplaintReopenView.as_view(),
        name="complaint-reopen",
    ),
]

urlpatterns += router.urls