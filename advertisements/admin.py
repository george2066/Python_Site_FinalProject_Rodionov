from django.contrib import admin

from advertisements.models import Category, Advertisement, RentalRequest, Transaction

# Register your models here.
admin.site.register(Category)
admin.site.register(Advertisement)
admin.site.register(RentalRequest)
admin.site.register(Transaction)
