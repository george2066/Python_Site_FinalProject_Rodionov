from rest_framework import serializers

from users.models import User
from django.core.validators import validate_email

from advertisements.models import Advertisement, Category, Transaction, Comment, Rent


class AdvertisementSerializer(serializers.ModelSerializer):
    # Дополнительно выводим название категории и имя автора
    category_name = serializers.CharField(
        source="category.name", read_only=True, allow_null=True
    )
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)
    author_email = serializers.EmailField(source="author.email", read_only=True)

    class Meta:
        model = Advertisement
        fields = [
            "id",
            "image_url",
            "title",
            "category",
            "category_name",
            "description",
            "price",
            "location",
            "contact_phone",
            "contact_email",
            "author",
            "author_name",
            "author_email",
            "sold",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "author"]

    def validate_price(self, value):
        """Проверка, что цена положительная"""
        if value <= 0:
            raise serializers.ValidationError("Цена должна быть больше нуля.")
        return value

    def create(self, validated_data):
        """При создании объявления автор устанавливается автоматически из контекста"""
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)


class UserSerializer(serializers.ModelSerializer):
    # Дополнительные поля для вывода (не из модели)
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "full_name",
            "email",
            "image_url",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
        ]
        read_only_fields = [
            "id",
            "date_joined",
            "last_login",
            "is_staff",
            "is_superuser",
        ]
        extra_kwargs = {"email": {"required": True}, "username": {"required": True}}

    def get_full_name(self, obj):
        """Возвращает полное имя пользователя (если реализовано в модели)"""
        return obj.get_full_name() or ""

    def validate_email(self, value):
        """Валидация email: уникальность и формат"""
        validate_email(value)  # Базовая валидация формата

        # Проверка уникальности email
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует."
            )
        return value.lower().strip()

    def validate_username(self, value):
        """Валидация username: непустое, не только пробелы"""
        if not value or not value.strip():
            raise serializers.ValidationError("Имя пользователя не может быть пустым.")
        return value.strip()

    def create(self, validated_data):
        """Создание пользователя с обязательным email"""
        validated_data["username"] = validated_data.get("username").strip()
        validated_data["email"] = validated_data.get("email").lower().strip()

        user = User(**validated_data)
        user.set_unusable_password()  # Для API-создания без пароля
        user.save()
        return user

    def update(self, instance, validated_data):
        """Обновление пользователя"""
        # Обработка email (с проверкой уникальности)
        email = validated_data.get("email")
        if email:
            email = email.lower().strip()
            if (
                User.objects.filter(email__iexact=email)
                .exclude(id=instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    {"email": "Email уже используется другим пользователем."}
                )
            instance.email = email

        # Обновление username
        username = validated_data.get("username")
        if username:
            instance.username = username.strip()

        # Обновление image_url
        image_url = validated_data.get("image_url")
        if image_url is not None:
            instance.image_url = image_url

        instance.save()
        return instance


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "date",
        ]
        read_only_fields = ["date"]  # auto_now поле — только для чтения

    def validate_name(self, value):
        """
        Проверка, что название категории не пустое и не состоит из пробелов.
        Также проверяем уникальность (если требуется).
        """
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Название категории не может быть пустым."
            )

        # Проверка уникальности (опционально)
        if Category.objects.filter(name__iexact=value.strip()).exists():
            raise serializers.ValidationError(
                "Категория с таким названием уже существует."
            )

        return value.strip()

    def create(self, validated_data):
        """
        При создании категории можно добавить дополнительную логику.
        Сейчас просто передаём данные в базовый метод.
        """
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        При обновлении категории можно добавить логику.
        Сейчас просто передаём данные в базовый метод.
        """
        return super().update(instance, validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    rent_id = serializers.PrimaryKeyRelatedField(
        source='rent',
        queryset=Rent.objects.all(),
        read_only=False
    )
    transaction_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    advertisement_price = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id',
            'transaction_date',
            'rent_id',
            'created_at',
            'advertisement_price',
        ]

    def get_advertisement_price(self, obj):
        # Получение цены из связанной аренды через rent
        if obj.rent and obj.rent.advertisement:
            return obj.rent.advertisement.price
        return None


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    advertisement = serializers.PrimaryKeyRelatedField(read_only=True)
    create_at = serializers.DateTimeField(read_only=True)
    update_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "advertisement",
            "comment",
            "create_at",
            "update_at",
        ]

    def validate_comment(self, value):
        """
        Проверка, что комментарий не пустой и не состоит из одних пробелов.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Комментарий не может быть пустым.")
        return value.strip()

    def create(self, validated_data):
        """
        Создание комментария с текущим пользователем и объявлением.
        Можно переопределить, если нужно автоматически присваивать user и advertisement.
        """
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["user"] = request.user
            # Предположим, что advertisement передается в контексте или через параметры
            # Или можно оставить ее для установки в view
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Обновление комментария.
        """
        return super().update(instance, validated_data)


class RentSerializer(serializers.ModelSerializer):
    advertisement_id = serializers.PrimaryKeyRelatedField(
        source='advertisement',
        queryset=Advertisement.objects.all(),
        read_only=False
    )
    renter_id = serializers.PrimaryKeyRelatedField(
        source='renter',
        queryset=User.objects.all(),
        read_only=False
    )
    from_date = serializers.DateField(format="%Y-%m-%d")
    to_date = serializers.DateField(format="%Y-%m-%d")
    create_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    update_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Rent
        fields = [
            'id',
            'advertisement_id',
            'renter_id',
            'from_date',
            'to_date',
            'payed',
            'create_at',
            'update_at',
        ]
