from rest_framework.routers import DefaultRouter

from .views import (
    ComplaintAssignmentViewSet,
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

urlpatterns = router.urls