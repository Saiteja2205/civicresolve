from django.urls import path

from organizations.views import ActiveCategoryListView


urlpatterns = [
    path(
        "categories/",
        ActiveCategoryListView.as_view(),
        name="active-category-list",
    ),
]