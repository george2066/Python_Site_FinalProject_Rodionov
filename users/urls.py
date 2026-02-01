from django.urls import path

from users.views import UserDetailView

urlpatterns = [
    path("profile/", UserDetailView.as_view(), name='profile'),
]