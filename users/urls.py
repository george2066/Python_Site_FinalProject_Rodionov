from django.urls import path

from users.views import UserDetailView, UserUpdateView, UserDeleteView

urlpatterns = [
    path("profile/", UserDetailView.as_view(), name='profile'),
    path('profile/edit/', UserUpdateView.as_view(), name='profile-update'),
    path('profile/delete/', UserDeleteView.as_view(), name='profile-delete'),
]