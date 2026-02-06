from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AdvertisementViewSet
from .views import CategoryViewSet
from .views import CommentViewSet
from .views import RentViewSet
from .views import TransactionViewSet
from .views import UserViewSet

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
