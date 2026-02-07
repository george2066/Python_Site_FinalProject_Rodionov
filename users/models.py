from django.contrib.auth.models import AbstractUser
from django.db import models

from users import avatar_default


# Create your models here.
class User(AbstractUser):
    image_url = models.URLField(max_length=500, default=avatar_default)
    email = models.EmailField(unique=True, verbose_name="Адрес электронной почты")
    telegram = models.CharField(max_length=255, null=True, blank=True)
    chat_id = models.BigIntegerField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username
