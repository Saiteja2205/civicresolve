from django.urls import path

from organizations.views import (
    ActiveCategoryListView,
    ActiveDepartmentListView,
    ActiveOfficerListView,
)


urlpatterns = [
    path(
        "categories/",
        ActiveCategoryListView.as_view(),
        name="active-category-list",
    ),
    path(
        "departments/",
        ActiveDepartmentListView.as_view(),
        name="active-department-list",
    ),
    path(
        "officers/",
        ActiveOfficerListView.as_view(),
        name="active-officer-list",
    ),
]