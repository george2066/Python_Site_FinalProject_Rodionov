from django.db import models

from advertisements.managers import CategoryManager, AdvertisementManager, RentalRequestManager, TransactionManager
from users.models import User

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now=True)
    objects = CategoryManager()

    def __str__(self):
        return self.name

class Advertisement(models.Model):
    image_url = models.URLField(max_length=200, blank=True, null=True)
    title = models.CharField(max_length=200, verbose_name="Название")
    category = models.ForeignKey(Category, models.SET_NULL, null=True, blank=True, verbose_name="Категория")
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    location = models.CharField(max_length=255, verbose_name="Местоположение")
    available_from = models.DateField(verbose_name="Доступно с")
    available_to = models.DateField(verbose_name="Доступно до")
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name="Контактный телефон")
    contact_email = models.EmailField(blank=True, verbose_name="Контактный email") #Добавил поле email
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='advertisements', verbose_name="Автор")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    objects = AdvertisementManager()

    class Meta:
        verbose_name = "Объявление"
        verbose_name_plural = "Объявления"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def is_available(self, date):
        return self.available_from <= date <= self.available_to
    
class RentalRequest(models.Model):
    start_date = models.DateField(verbose_name="Дата начала аренды")
    end_date = models.DateField(verbose_name="Дата окончания аренды")
    quantity = models.PositiveIntegerField(verbose_name="Количество запрашиваемых предметов")
    comment = models.TextField(blank=True, verbose_name="Комментарии")
    requester = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rental_requests', verbose_name="Заявитель")
    advertisement = models.ForeignKey(Advertisement, on_delete=models.CASCADE, related_name='rental_requests', verbose_name="Объявление")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    objects = RentalRequestManager()

    class Meta:
        verbose_name = "Запрос на аренду"
        verbose_name_plural = "Запросы на аренду"
        ordering = ['-created_at']

    def __str__(self):
        return f"Запрос на аренду с {self.start_date} по {self.end_date}"


class Transaction(models.Model):
    transaction_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата транзакции")
    rental_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Стоимость аренды")
    rental_start = models.DateField(verbose_name="Начало периода аренды")
    rental_end = models.DateField(verbose_name="Конец периода аренды")
    rental_request = models.ForeignKey(RentalRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions", verbose_name="Запрос на аренду")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions', verbose_name="Пользователь")
    advertisement = models.ForeignKey(Advertisement, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions", verbose_name="Объявление")

    objects = TransactionManager()

    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"
        ordering = ['-transaction_date']

    def __str__(self):
        return f"Транзакция от {self.transaction_date} на сумму {self.rental_cost}"
