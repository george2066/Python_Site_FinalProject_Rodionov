from django.urls import path

from advertisements.views import AdvertisementsUserListView, AdvertisementDetailView
urlpatterns = [
    path("advertisements", AdvertisementsUserListView.as_view(), name='advertisements'),
    path("advertisement/<int:pk>/", AdvertisementDetailView.as_view(), name='advertisement'),

]