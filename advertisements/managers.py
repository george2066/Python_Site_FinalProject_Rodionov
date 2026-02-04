from django.db import models
from django.urls import reverse


class AdvertisementManager(models.Manager):
    template_name = r"advertisements\advertisement_list.html"

    def get_absolute_url(self):
        return reverse("advertisement", args=[self.pk])

    def for_user(self, user):
        return self.get_queryset().filter(author_id=user)


class CategoryManager(models.Manager):
    pass


class TransactionManager(models.Manager):
    pass


class CommentManager(models.Manager):
    pass

class RentManager(models.Manager):
    pass

class LocationManager(models.Manager):
    pass
