from django import forms

from advertisements.models import Advertisement
from advertisements.models import Comment
from advertisements.models import Rent

"""
Variant №1

class AdvertisementForm(forms.ModelForm):
    city = forms.CharField(max_length=255, required=False)
    street = forms.CharField(max_length=255, required=False)
    house = forms.CharField(max_length=255, required=False)

    class Meta:
        model = Advertisement
        fields = ['image_url', 'title', 'category', 'description', 'price', 'location', 'city', 'street', 'house']
"""


class AdvertisementForm(forms.ModelForm):
    class Meta:
        model = Advertisement
        fields = ["image_url", "title", "category", "description", "price", "location"]
        widgets = {
            "location": forms.HiddenInput(),  # или отдельные поля для города, улицы, дома
        }


class CommentForm(forms.ModelForm):
    comment = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Напишите ваш комментарий...",
                "class": "form-control",
            }
        ),
        max_length=510,
        label="Комментарий",
    )

    class Meta:
        model = Comment
        fields = ["comment"]


class RentForm(forms.ModelForm):
    class Meta:
        model = Rent
        fields = ["from_date", "to_date"]
        widgets = {
            "from_date": forms.DateInput(attrs={"type": "date"}),
            "to_date": forms.DateInput(attrs={"type": "date"}),
        }
