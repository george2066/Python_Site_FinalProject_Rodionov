from django.urls import path

from advertisements.views import AdvertisementsUserListView, AdvertisementDetailView, AdvertisementCreateView, AdvertisementDeleteView, AdvertisementUpdateView
urlpatterns = [
    path("advertisements", AdvertisementsUserListView.as_view(), name='advertisements'),
    path("advertisement/<int:pk>/", AdvertisementDetailView.as_view(), name='advertisement'),
    path("advertisement/add/", AdvertisementCreateView.as_view(), name='advertisement-add'),
    path("advertisement/delete/<int:pk>/", AdvertisementDeleteView.as_view(), name='advertisement-delete'),
    path("advertisement/update/<int:pk>/", AdvertisementUpdateView.as_view(), name='advertisement-update'),
]