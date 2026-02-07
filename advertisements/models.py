from django.db import models
from django.utils.timezone import now

from advertisements.managers import AdvertisementManager
from advertisements.managers import CategoryManager
from advertisements.managers import CommentManager
from advertisements.managers import LocationManager
from advertisements.managers import RentManager
from advertisements.managers import TransactionManager
from users.models import User


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now=True)
    objects = CategoryManager()

    def __str__(self):
        return self.name


class Location(models.Model):
    city = models.CharField(max_length=255, verbose_name="Город")
    street = models.CharField(max_length=255, verbose_name="Улица")
    home = models.CharField(max_length=255, verbose_name="Дом")
    apartment = models.CharField(max_length=255, verbose_name="Квартира")

    objects = LocationManager()


class Advertisement(models.Model):
    image_url = models.URLField(max_length=200, blank=True, null=True)
    title = models.CharField(max_length=200, verbose_name="Название")
    category = models.ForeignKey(
        Category, models.SET_NULL, null=True, blank=True, verbose_name="Категория"
    )
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, verbose_name="Локация"
    )
    contact_phone = models.CharField(
        max_length=20, blank=True, verbose_name="Контактный телефон"
    )
    contact_email = models.EmailField(
        blank=True, verbose_name="Контактный email"
    )  # Добавил поле email
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="advertisements",
        verbose_name="Автор",
    )
    sold = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    is_approved = models.BooleanField(default=False)

    objects = AdvertisementManager()

    class Meta:
        verbose_name = "Объявление"
        verbose_name_plural = "Объявления"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Rent(models.Model):
    advertisement = models.ForeignKey(
        Advertisement, on_delete=models.CASCADE, verbose_name="Объявление"
    )
    renter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Съёмщик",
        related_name="related_renter",
    )
    from_date = models.DateField(verbose_name="Начало аренды")
    to_date = models.DateField(verbose_name="Окончание аренды")
    overdue = models.BooleanField(default=False, verbose_name="Просрочено")
    payed = models.BooleanField(default=False)
    create_at = models.DateTimeField(auto_now=True, verbose_name="Дата создания")
    update_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    objects = RentManager()

    def save(self, *args, **kwargs):
        if not self.pk or kwargs.get(
            "force_update", False
        ):  # проверяем, не новый ли объект
            today = (
                now().date()
            )  # используем timezone.now(), чтобы учитывать часовой пояс
            self.overdue = today > self.to_date
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Аренда  пользователя {self.renter.__str__()} к объявлению {self.advertisement}"


class Transaction(models.Model):
    transaction_date = models.DateTimeField(default=now, verbose_name="Дата транзакции")
    rent = models.ForeignKey(
        Rent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
        verbose_name="Аренда",
    )
    created_at = models.DateTimeField(verbose_name="Дата создания", default=now)

    objects = TransactionManager()

    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"
        ordering = ["-transaction_date"]

    def __str__(self):
        if self.rent and hasattr(self.rent, "advertisement"):
            price = self.rent.advertisement.price
        else:
            price = "неизвестно"
        return f"Транзакция от {self.transaction_date} на сумму {price}"


class Comment(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор",
    )
    advertisement = models.ForeignKey(
        Advertisement,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Объявление",
    )
    comment = models.CharField(max_length=510)
    create_at = models.DateTimeField(auto_now=True, verbose_name="Дата создания")
    update_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    objects = CommentManager()

    def __str__(self):
        return f"Комментарий от пользователя {self.user.__str__()} к объявлению {self.advertisement.__str__()}"
