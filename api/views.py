from django.shortcuts import render
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from advertisements.models import Advertisement
from .serializers import AdvertisementSerializer

# Create your views here.


class AdvertisementViewSet(ModelViewSet):
    """
    API для управления объявлениями (CRUD).
    """

    queryset = Advertisement.objects.select_related("category", "author").all()
    serializer_class = AdvertisementSerializer
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["title", "description", "location"]
    ordering_fields = ["price", "created_at", "updated_at"]
    ordering = ["-created_at"]  # По умолчанию — новые сверху
    pagination_class = None  # Можно подключить PageNumberPagination

    # Права доступа
    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated()]
        return [IsAuthenticated()]  # Или [] для публичного чтения

    def perform_create(self, serializer):
        """При создании автор = текущий пользователь"""
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        """При обновлении проверяем, что автор — текущий пользователь (или админ)"""
        instance = self.get_object()
        if instance.author != self.request.user and not self.request.user.is_staff:
            self.permission_denied(
                self.request, message="Вы не можете редактировать это объявление."
            )
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """Удаление с проверкой прав"""
        instance = self.get_object()
        if instance.author != request.user and not request.user.is_staff:
            return Response(
                {"error": "Вы не можете удалить это объявление."},
                status=status.HTTP_403_FORBIDDEN,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="my")
    def my_advertisements(self, request):
        """Возвращает объявления текущего пользователя"""
        queryset = self.filter_queryset(self.get_queryset().filter(author=request.user))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
