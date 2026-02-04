import os
import json
import logging
import requests
from datetime import timedelta


from yookassa import Configuration, Payment


from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DetailView,
    DeleteView,
    TemplateView,
)


from advertisements.forms import CommentForm, RentForm
from advertisements.models import Advertisement, Transaction, Comment, Location, Rent
from diplom import settings
from users.models import User

TEMPLATE_DIR = "advertisements"
logger = logging.getLogger(__name__)


def home(request):
    context = {
        "title": "Домашняя страница",
        "heading": "Добро пожаловать на сайт!",
        "content": "Это контент домашней страницы",
    }
    return render(request, "diplom/home.html", context)


def contact(request):
    return render(request, "contact.html")


def buy_rent(request, ad_id, rent_id):
    # Получаем объявление
    advertisement = get_object_or_404(Advertisement, id=ad_id)

    # Настраиваем подключение к ЮКассе
    Configuration.account_id = settings.YOOKASSA_SHOP_ID
    Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

    # Параметры платежа
    payment_data = {
        "amount": {
            "value": str(advertisement.price),  # Сумма из объявления
            "currency": "RUB",
        },
        "confirmation": {
            "type": "redirect",
            "return_url": request.build_absolute_uri(reverse("payment_success")),
        },
        "capture": True,
        "description": f"Оплата объявления: {advertisement.title}",
        "metadata": {"advertisement_id": str(ad_id), "user_id": str(request.user.id)},
    }

    try:
        # Создаём платёж
        payment = Payment.create(payment_data)

        # Сохраняем ID платежа в сессии (для проверки позже)
        request.session['advertisement_id'] = ad_id
        request.session["payment_id"] = payment.id
        request.session["rent_id"] = rent_id

        # Переводим пользователя на страницу оплаты
        return redirect(payment.confirmation.confirmation_url)

    except Exception as e:
        messages.error(request, f"Ошибка при создании платежа: {e}")
        return redirect("advertisement", ad_id=ad_id)


def payment_success(request):
    payment_id = request.session.get("payment_id")
    rent_id = request.session.get("rent_id")
    advertisement_id = request.session.get("advrtisement_id")

    if not payment_id:
        messages.error(request, "Платёж не найден.")
        return redirect("home")

    try:
        payment = Payment.find_one(payment_id)

        if payment.status == "succeeded":
            metadata = payment.metadata
            advertisement_id = metadata.get("advertisement_id")
            rent_id_from_metadata = metadata.get("rent_id")  # Можно использовать, если есть
            advertisement_id_from_metadata = metadata.get("advertisement_id")  # Можно использовать, если есть

            # Или использовать rent_id из сессии
            rent_id_to_use = rent_id or rent_id_from_metadata
            advertisement_id_to_use = advertisement_id or advertisement_id_from_metadata

            # Обновляем объявление
            advertisement = get_object_or_404(Advertisement, id=advertisement_id_to_use)
            advertisement.sold = True
            advertisement.save()

            # Обновляем аренду
            rent = get_object_or_404(Rent, id=rent_id_to_use)
            rent.payed = True
            rent.save()

            # Создаем транзакцию
            transaction = Transaction.objects.create(rent=rent)

            messages.success(
                request, f"Оплата прошла успешно! ID транзакции: {transaction.id}"
            )
        else:
            messages.error(request, f"Платёж не завершён (статус: {payment.status})")
    except Exception as e:
        logger.error(f"Ошибка при обработке платежа {payment_id}: {e}")
        messages.error(request, f"Ошибка проверки платежа: {e}")

    # Очистка сессии
    if "payment_id" in request.session:
        del request.session["payment_id"]
    if "rent_id" in request.session:
        del request.session["rent_id"]

    # возвращает список объявлений или другую страницу
    advertisements = Advertisement.objects.all()
    context = {"advertisements": advertisements}

    return render(
        request,
        os.path.join(TEMPLATE_DIR, "advertisement_list.html"),
        context,
    )


@csrf_exempt
def yookassa_webhook(request):
    if request.method == "POST":
        data = json.loads(request.body)
        # Обрабатываем событие (например, payment.succeeded)
        if data["event"] == "payment.succeeded":
            payment = data["object"]
            # Обновляем БД: отмечаем заказ как оплаченный
        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "Invalid request"}, status=400)


def approve_ad(request):
    # Получаем все неодобренные объявления
    advertisements = Advertisement.objects.filter(is_approved=False)
    advertisemtnts = advertisements.filter(sold=False)

    if request.method == "POST":
        # Получаем список ID из чекбоксов (name="approve_ad")
        approved_ids = request.POST.getlist("approve_ad")

        # Обновляем только выбранные объявления
        Advertisement.objects.filter(id__in=approved_ids).update(is_approved=True)

        # Добавляем сообщение об успехе (опционально)
        messages.success(request, f"Одобрено {len(approved_ids)} объявлений.")

        return redirect("advertisements")  # Редирект на ту же страницу

    return render(
        request,
        os.path.join(TEMPLATE_DIR, "advertisement_approve.html"),
        {"advertisements": advertisements},
    )


@csrf_exempt
@require_POST
def edit_comment(request):
    data = json.loads(request.body)
    comment_id = data.get("comment_id")
    comment_text = data.get("comment")
    try:
        comment = Comment.objects.get(id=comment_id, user=request.user)
        comment.comment = comment_text
        comment.save()
        return JsonResponse({"success": True})
    except Exception:
        return JsonResponse(
            {"success": False, "error": "Комментарий не найден или недоступен"}
        )


@csrf_exempt
def delete_comment(request):
    if request.method == "POST":
        data = json.loads(request.body)
        comment_id = data.get("comment_id")
        try:
            comment = Comment.objects.get(id=comment_id, user=request.user)
            comment.delete()
            return JsonResponse({"success": True})
        except Exception:
            return JsonResponse(
                {"success": False, "error": "Комментарий не найден или недоступен"}
            )
    return JsonResponse({"success": False, "error": "Некорректный метод"})

def filter_advertisements():
    advertisements = Advertisement.objects.all()
    advertisements = advertisements.filter(sold=False)
    advertisements = advertisements.filter(is_approved=True)
    return advertisements


# Create your views here.
class AdvertisementsUserListView(LoginRequiredMixin, ListView):
    login_url = reverse_lazy("account_login")

    def get_queryset(self):
        return Advertisement.objects.for_user(self.request.user)


class AdvertisementDetailView(DetailView):
    login_url = reverse_lazy("account_login")
    model = Advertisement

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        advertisement = self.object

        # Добавляем данные объявления
        context["image"] = advertisement.image_url
        context["title"] = advertisement.title
        context["category"] = advertisement.category
        context["author_id"] = advertisement.author
        context["description"] = advertisement.description

        # Форма для комментария
        context["comment_form"] = CommentForm()

        # Список комментариев к объявлению
        context["comments"] = advertisement.comments.all().order_by("-create_at")

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.advertisement = self.object
            comment.save()
            return redirect(self.get_success_url())

        # Если форма невалидна — возвращаем в контекст с ошибками
        context = self.get_context_data()
        context["comment_form"] = form
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse("advertisement", kwargs={"pk": self.object.pk})


class AdvertisementCreateView(LoginRequiredMixin, CreateView):
    login_url = reverse_lazy("account_login")
    model = Advertisement
    fields = [
        "image_url",
        "title",
        "category",
        "description",
        "price",
    ]

    def form_valid(self, form):
        form.instance.author = self.request.user
        # Создаем или обновляем Location
        location = Location.objects.create(
            city=form.cleaned_data.get('city', ''),
            street=form.cleaned_data.get('street', ''),
            home=form.cleaned_data.get('home', ''),
        )
        form.instance.location = location
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("advertisements")


class AdvertisementDeleteView(LoginRequiredMixin, DeleteView):
    login_url = reverse_lazy("account_login")
    model = Advertisement
    success_url = reverse_lazy("advertisements")

    def get_queryset(self):
        return Advertisement.objects.for_user(self.request.user)


class AdvertisementUpdateView(LoginRequiredMixin, UpdateView):
    login_url = reverse_lazy("account_login")
    model = Advertisement
    fields = [
        "image_url",
        "title",
        "category",
        "description",
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update advertisement"
        return context

    def get_success_url(self):
        return reverse("advertisements")


class HomePageView(TemplateView):
    template_name = os.path.join(TEMPLATE_DIR, "advertisement_list.html")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем все объявления
        advertisements = filter_advertisements()

        # Настройка пагинации (10 объявлений на страницу)
        paginator = Paginator(advertisements, settings.PAGE_ENTITY)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["advertisements"] = page_obj
        context["paginator"] = paginator
        context["page_obj"] = page_obj

        return context


class SearchResultsView(ListView):
    model = Advertisement
    context_object_name = "advertisements"
    paginate_by = settings.PAGE_ENTITY  # 10 объявлений на страницу

    def get_queryset(self):
        query = self.request.GET.get("q")
        clear = self.request.GET.get("clear")

        if clear == "true":
            advertisements = filter_advertisements()
            return advertisements

        if query:
            return Advertisement.objects.filter(Q(title__icontains=query))
        return Advertisement.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        return context



class RentCreateView(CreateView):
    model = Rent
    form_class = RentForm
    template_name = os.path.join(TEMPLATE_DIR, "advertisement_rent_form.html")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['advertisement'] = Advertisement.objects.get(pk=self.kwargs['ad_id'])
        return context

    def form_valid(self, form):
        # Устанавливаем связь с объявлением
        ad_id = self.kwargs['ad_id']
        advertisement = Advertisement.objects.get(pk=ad_id)
        form.instance.advertisement = advertisement
        form.instance.renter = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        # После сохранения аренды перенаправляем на страницу оплаты
        return reverse('buy_rent', kwargs={
            'ad_id': self.object.advertisement.id,
            'rent_id': self.object.id
        })