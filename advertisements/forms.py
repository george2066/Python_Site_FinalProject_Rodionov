from django import forms

from advertisements.models import Advertisement
from advertisements.models import Comment
from advertisements.models import Location
from advertisements.models import Rent


class AdvertisementForm(forms.ModelForm):
    city = forms.CharField(max_length=255, required=False)
    street = forms.CharField(max_length=255, required=False)
    home = forms.CharField(max_length=255, required=False)
    apartment = forms.CharField(max_length=255, required=False)

    class Meta:
        model = Advertisement
        fields = ["image_url", "title", "category", "description", "price"]
        widgets = {
            "location": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            loc = self.instance.location
            self.initial.update({
                "city": loc.city,
                "street": loc.street,
                "home": loc.home,
                "apartment": loc.apartment,
            })

    def clean(self):
        cleaned_data = super().clean()
        city = cleaned_data.get("city")
        street = cleaned_data.get("street")
        home = cleaned_data.get("home")
        if not city or not street or not home:
            raise forms.ValidationError("Заполните город, улицу и дом")
        return cleaned_data

    def save(self, *args, **kwargs):
        location_data = {
            "city": self.cleaned_data["city"],
            "street": self.cleaned_data["street"],
            "home": self.cleaned_data["home"],
            "apartment": self.cleaned_data.get("apartment", ""),
        }
        if self.instance and self.instance.pk and self.instance.location_id:
            loc = self.instance.location
            for key, value in location_data.items():
                setattr(loc, key, value)
            loc.save()
        else:
            loc = Location.objects.create(**location_data)
            self.instance.location = loc
        return super().save(*args, **kwargs)


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
