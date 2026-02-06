from django.contrib.auth.models import AbstractUser
from django.db import models

from users import avatar_default


# Create your models here.
class User(AbstractUser):
    image_url = models.URLField(max_length=400, default=avatar_default)
    email = models.EmailField(unique=True, verbose_name="Адрес электронной почты")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username
