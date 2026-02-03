from django import forms

from advertisements.models import Advertisement, Comment


class AdvertisementForm(forms.ModelForm):
    class Meta:
        model = Advertisement
        fields = ["title", "image_url", "description"]


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
