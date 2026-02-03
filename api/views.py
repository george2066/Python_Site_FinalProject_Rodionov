from django.contrib.auth import get_user_model

from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from advertisements.models import Category, Transaction, Advertisement, Comment
from .serializers import CategorySerializer, TransactionSerializer, UserSerializer, AdvertisementSerializer, \
    CommentSerializer

User = get_user_model()


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


class UserViewSet(ModelViewSet):
    """
    API для управления пользователями (CRUD).
    """

    queryset = User.objects.only(
        "id",
        "username",
        "email",
        "image_url",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
    )
    serializer_class = UserSerializer
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["username", "email"]
    ordering_fields = ["date_joined", "username"]
    ordering = ["-date_joined"]
    pagination_class = None  # Подключите PageNumberPagination при необходимости

    def get_permissions(self):
        """
        Права доступа:
        - Создание: только админ.
        - Чтение/обновление/удаление: админ или сам пользователь.
        """
        if self.action == "create":
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """При создании пользователя пароль задаётся отдельно (не через API)"""
        user = serializer.save()
        user.set_unusable_password()  # Пароль задаётся через админку/другой механизм
        user.save()

    def perform_update(self, serializer):
        """Обновление: только сам пользователь или админ"""
        instance = self.get_object()
        if instance != self.request.user and not self.request.user.is_staff:
            self.permission_denied(
                self.request, message="Вы не можете редактировать этого пользователя."
            )
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """Удаление: только админ или сам пользователь (если не суперпользователь)"""
        instance = self.get_object()
        if instance == request.user:
            if instance.is_superuser:
                return Response(
                    {"error": "Суперпользователя нельзя удалить через API."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            # Пользователь удаляет сам себя
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        elif request.user.is_staff:
            # Админ удаляет пользователя
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {"error": "У вас нет прав на удаление этого пользователя."},
                status=status.HTTP_403_FORBIDDEN,
            )

    @action(detail=False, methods=["get"], url_path="me")
    def current_user(self, request):
        """Возвращает данные текущего авторизованного пользователя"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class CategoryViewSet(ModelViewSet):
    """
    API для управления категориями (CRUD).
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["name"]
    ordering_fields = ["name", "date"]
    ordering = ["name"]  # Сортировка по умолчанию
    pagination_class = None  # Подключите PageNumberPagination при необходимости

    def get_permissions(self):
        """
        Права доступа:
        - Создание/обновление/удаление: только админ.
        - Чтение: все авторизованные пользователи.
        """
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Дополнительная логика при создании (если нужна)"""
        serializer.save()

    def perform_update(self, serializer):
        """Дополнительная логика при обновлении (если нужна)"""
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """Удаление категории с проверкой"""
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except Exception as e:
            return Response(
                {"error": f"Не удалось удалить категорию: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="active")
    def active_categories(self, request):
        """Возвращает активные категории (если есть поле is_active)"""
        # Если в модели есть поле is_active, используйте:
        # queryset = self.filter_queryset(self.get_queryset().filter(is_active=True))
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TransactionViewSet(ModelViewSet):
    """
    API для управления транзакциями (CRUD).
    """

    queryset = Transaction.objects.select_related("user", "advertisement").all()
    serializer_class = TransactionSerializer
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["user__username", "advertisement__title"]
    ordering_fields = ["transaction_date", "created_at"]
    ordering = ["-transaction_date"]  # Новые транзакции сверху
    pagination_class = None  # Подключите PageNumberPagination при необходимости

    def get_permissions(self):
        """
        Права доступа:
        - Создание/обновление/удаление: только админ или владелец транзакции (если логика позволяет).
        - Чтение: все авторизованные пользователи (или только админ, если требуется).
        """
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]  # Только админ может изменять транзакции
        return [IsAuthenticated()]  # Чтение доступно всем авторизованным

    def perform_create(self, serializer):
        """Дополнительная логика при создании (если нужна)"""
        serializer.save()

    def perform_update(self, serializer):
        """Дополнительная логика при обновлении (если нужна)"""
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """Удаление транзакции с проверкой прав"""
        instance = self.get_object()
        # Пример: только админ может удалять транзакции
        if not request.user.is_staff:
            return Response(
                {"error": "У вас нет прав на удаление этой транзакции."},
                status=status.HTTP_403_FORBIDDEN,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="my")
    def my_transactions(self, request):
        """Возвращает транзакции текущего пользователя"""
        queryset = self.filter_queryset(self.get_queryset().filter(user=request.user))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="details")
    def transaction_details(self, request, pk=None):
        """Возвращает детали транзакции с дополнительной информацией"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class CommentViewSet(ModelViewSet):
    """
    API для управления комментариями (CRUD).
    """

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["comment"]
    ordering_fields = ["create_at", "update_at"]
    ordering = ["-create_at"]  # сортировка по умолчанию — по дате создания, newest first

    def get_permissions(self):
        """
        Права доступа:
        - Создание/обновление/удаление: только админ.
        - Чтение: все авторизованные пользователи.
        """
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """
        При создании комментария автоматически присваивается текущий пользователь.
        """
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """
        Можно добавить дополнительные проверки или логику при обновлении.
        """
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """
        Удаление комментария с проверкой прав.
        """
        instance = self.get_object()
        if request.user != instance.user and not request.user.is_staff:
            return Response(
                {"detail": "Нет прав на удаление этого комментария."},
                status=status.HTTP_403_FORBIDDEN
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="my-comments")
    def my_comments(self, request):
        """
        Получить все комментарии текущего пользователя.
        """
        queryset = self.filter_queryset(self.get_queryset().filter(user=request.user))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
