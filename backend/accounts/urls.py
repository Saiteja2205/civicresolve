from django.urls import path

from .views import CurrentUserView
from .views import UserProfileView

urlpatterns = [
    path(
        "me/",
        CurrentUserView.as_view(),
        name="current-user",
    ),
    path(
    "profile/",
    UserProfileView.as_view(),
    name="user-profile",
    ),
]