from django.contrib import admin

from advertisements.models import Advertisement
from advertisements.models import Category
from advertisements.models import Comment
from advertisements.models import Location
from advertisements.models import Rent
from advertisements.models import Transaction

# Register your models here.
admin.site.register(Category)
admin.site.register(Advertisement)
admin.site.register(Transaction)
admin.site.register(Rent)
admin.site.register(Location)
admin.site.register(Comment)
