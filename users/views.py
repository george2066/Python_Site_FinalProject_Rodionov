import os

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import UpdateView

from advertisements.models import Advertisement
from diplom import settings
from users.models import User


@login_required
@require_http_methods(["GET"])
def load_more_advertisements(request):
    user = request.user
    page = int(request.GET.get("page", settings.PAGE_ENTITY))
    per_page = settings.PAGE_ENTITY

    # Все объявления пользователя, кроме первого (которое уже показано)
    all_ads = Advertisement.objects.filter(author=user).order_by("-created_at")[
        settings.PAGE_ENTITY :
    ]

    start = (page - 1) * per_page
    end = start + per_page

    more_ads = all_ads[start:end]

    data = {
        "advertisements": [
            {
                "id": ad.id,
                "title": ad.title,
                "url": request.build_absolute_uri(f"/advertisement/{ad.id}/"),
            }
            for ad in more_ads
        ],
        "has_more": len(all_ads) > end,
    }
    return JsonResponse(data)


# Create your views here.
class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = os.path.join("users", "profile.html")

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object

        # Изначально показываем только 1 объявление
        advertisements = Advertisement.objects.filter(author=user).order_by(
            "-created_at"
        )[: settings.PAGE_ENTITY]
        context["advertisements"] = advertisements
        context["total_advertisements"] = Advertisement.objects.filter(
            author=user
        ).count()
        context["pagination"] = settings.PAGE_ENTITY
        context["image"] = user.image_url
        context["username"] = user.username
        context["email"] = user.email
        context["first_name"] = user.first_name
        context["last_name"] = user.last_name
        context["telegram"] = user.telegram

        return context


class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    fields = [
        "username",
        "email",
        "first_name",
        "last_name",
        "image_url",
        "telegram",
        "phone",
    ]
    template_name = os.path.join("users", "profile_update.html")
    success_url = reverse_lazy("profile")

    def get_object(self, queryset=None):
        return self.request.user

    def test_func(self):
        user = self.get_object()
        return self.request.user == user


class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = os.path.join("users", "profile_confirm_delete.html")
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return self.request.user

    def test_func(self):
        user = self.get_object()
        return self.request.user == user
