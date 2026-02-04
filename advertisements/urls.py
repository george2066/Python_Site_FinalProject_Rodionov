from django.urls import path

from advertisements.views import (
    AdvertisementsUserListView,
    AdvertisementDetailView,
    AdvertisementCreateView,
    AdvertisementDeleteView,
    AdvertisementUpdateView,
    HomePageView,
    SearchResultsView,
    RentCreateView,
    buy_rent,
    payment_success,
    approve_ad,
    edit_comment,
    delete_comment,
)


urlpatterns = [
    path("search/", SearchResultsView.as_view(), name="search_results"),
    path("advertisements", HomePageView.as_view(), name="advertisements"),
    path(
        "advertisements/my",
        AdvertisementsUserListView.as_view(),
        name="advertisements-user",
    ),
    path(
        "advertisement/<int:pk>/",
        AdvertisementDetailView.as_view(),
        name="advertisement",
    ),
    path(
        "advertisement/add/",
        AdvertisementCreateView.as_view(),
        name="advertisement-add",
    ),
    path(
        "advertisement/delete/<int:pk>/",
        AdvertisementDeleteView.as_view(),
        name="advertisement-delete",
    ),
    path(
        "advertisement/update/<int:pk>/",
        AdvertisementUpdateView.as_view(),
        name="advertisement-update",
    ),
    path("advertisements/approve/", approve_ad, name="approve"),
    path(
        "advertisement/<int:ad_id>/rent/add/",
        RentCreateView.as_view(),
        name="rent_create",
    ),
    path("advertisement/<int:ad_id>/<int:rent_id>/buy/", buy_rent, name="buy_rent"),
    path("payment/success/", payment_success, name="payment_success"),
    path("comments/edit/", edit_comment, name="edit_comment"),
    path("comments/delete/", delete_comment, name="delete_comment"),
]
