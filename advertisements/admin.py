from django.contrib import admin

from advertisements.models import Category, Advertisement, Transaction

# Register your models here.
admin.site.register(Category)
admin.site.register(Advertisement)
admin.site.register(Transaction)
