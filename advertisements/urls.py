from django.urls import path

from advertisements.views import (
    AdvertisementsUserListView,
    AdvertisementDetailView,
    AdvertisementCreateView,
    AdvertisementDeleteView,
    AdvertisementUpdateView,
    HomePageView,
    SearchResultsView,
    buy_advertisement,
    payment_success,
    approve_ad,
    edit_comment,
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
    path("advertisements/approve", approve_ad, name="approve"),
    path("ad/<int:ad_id>/buy/", buy_advertisement, name="buy_advertisement"),
    path("payment/success/", payment_success, name="payment_success"),
    path('comments/edit/', edit_comment, name='edit_comment'),
]
