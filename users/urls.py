from django.urls import path

from users.views import load_more_advertisements
from users.views import UserDeleteView
from users.views import UserDetailView
from users.views import UserUpdateView

urlpatterns = [
    path("profile/", UserDetailView.as_view(), name="profile"),
    path("profile/edit/", UserUpdateView.as_view(), name="profile-update"),
    path("profile/delete/", UserDeleteView.as_view(), name="profile-delete"),
    path("load-more-ads/", load_more_advertisements, name="load_more_advertisements"),
]
