from django.urls import path

from .views import (
    CitizenRegistrationView,
    CurrentUserView,
    UserProfileView,
)

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
    path(
        "register/",
        CitizenRegistrationView.as_view(),
        name="citizen-register",
    ),
]