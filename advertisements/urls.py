from django.urls import path

from advertisements.views import AdvertisementsUserListView
urlpatterns = [
    path("advertisements", AdvertisementsUserListView.as_view(), name='advertisements'),

]