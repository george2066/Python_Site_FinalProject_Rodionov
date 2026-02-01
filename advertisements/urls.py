from django.urls import path

from advertisements.views import AdvertisementsUserListView, AdvertisementDetailView, AdvertisementCreateView
urlpatterns = [
    path("advertisements", AdvertisementsUserListView.as_view(), name='advertisements'),
    path("advertisement/<int:pk>/", AdvertisementDetailView.as_view(), name='advertisement'),
    path("advertisement/add/", AdvertisementCreateView.as_view(), name='advertisement-add'),
]