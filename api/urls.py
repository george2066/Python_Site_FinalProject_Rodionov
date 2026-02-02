from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdvertisementViewSet,
    UserViewSet,
    CategoryViewSet,
    TransactionViewSet,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"category", CategoryViewSet, basename="category")
router.register(r"advertisements", AdvertisementViewSet, basename="advertisement")
router.register(r"transaction", TransactionViewSet, basename="transaction")


urlpatterns = [
    path("api/", include(router.urls)),
]
