from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdvertisementViewSet,
    UserViewSet,
    CategoryViewSet,
    TransactionViewSet,
    CommentViewSet, RentViewSet,
)

router = DefaultRouter()

router.register(r"users", UserViewSet, basename="users")
router.register(r"category", CategoryViewSet, basename="category")
router.register(r"advertisements", AdvertisementViewSet, basename="advertisement")
router.register(r"transaction", TransactionViewSet, basename="transaction")
router.register(r"comment", CommentViewSet, basename="comment")
router.register(r"rent", RentViewSet, basename="rens")


urlpatterns = [
    path("api/", include(router.urls)),
]
