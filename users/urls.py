from django.urls import path

from users.views import (
    UserDetailView,
    UserUpdateView,
    UserDeleteView,
    load_more_advertisements,
)

urlpatterns = [
    path("profile/", UserDetailView.as_view(), name="profile"),
    path("profile/edit/", UserUpdateView.as_view(), name="profile-update"),
    path("profile/delete/", UserDeleteView.as_view(), name="profile-delete"),
    path("load-more-ads/", load_more_advertisements, name="load_more_advertisements"),
]
