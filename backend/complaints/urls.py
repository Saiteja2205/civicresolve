from rest_framework.routers import DefaultRouter

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
    basename="complaint-sla",
)


urlpatterns = router.urls