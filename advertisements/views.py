import json
import logging
import os

import pika
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic import UpdateView
from yookassa import Configuration
from yookassa import Payment

from advertisements.forms import AdvertisementForm
from advertisements.forms import CommentForm
from advertisements.forms import RentForm
from advertisements.models import Advertisement
from advertisements.models import Comment
from advertisements.models import Location
from advertisements.models import PaymentLog
from advertisements.models import Rent
from advertisements.models import Transaction
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
    advertisement = get_object_or_404(Advertisement, id=ad_id)

    Configuration.account_id = settings.YOOKASSA_SHOP_ID
    Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

    payment_data = {
        "amount": {
            "value": str(advertisement.price),
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
        payment = Payment.create(payment_data)

        request.session["advertisement_id"] = ad_id
        request.session["payment_id"] = payment.id
        request.session["rent_id"] = rent_id

        return redirect(payment.confirmation.confirmation_url)

    except Exception as e:
        messages.error(request, f"Ошибка при создании платежа: {e}")
        return redirect("advertisement", ad_id=ad_id)


def payment_success(request):
    payment_id = request.session.get("payment_id")
    rent_id = request.session.get("rent_id")
    advertisement_id = request.session.get("advertisement_id")

    if not payment_id:
        messages.error(request, "Платёж не найден.")
        return redirect("home")

    if PaymentLog.objects.filter(payment_id=payment_id).exists():
        messages.warning(request, "Этот платёж уже был обработан.")
        return redirect("advertisements")

    try:
        payment = Payment.find_one(payment_id)

        if payment.status == "succeeded":
            metadata = payment.metadata
            advertisement_id = metadata.get("advertisement_id")
            rent_id_from_metadata = metadata.get("rent_id")
            advertisement_id_from_metadata = metadata.get("advertisement_id")

            rent_id_to_use = rent_id or rent_id_from_metadata
            advertisement_id_to_use = advertisement_id or advertisement_id_from_metadata

            advertisement = get_object_or_404(Advertisement, id=advertisement_id_to_use)
            advertisement.sold = True
            advertisement.save()

            rent = get_object_or_404(Rent, id=rent_id_to_use)
            rent.payed = True
            rent.save()

            renter = rent.renter
            queue = "rent_create"
            transaction = Transaction.objects.create(
                rent=rent, created_at=timezone.now()
            )

            PaymentLog.objects.create(payment_id=payment_id)

            json_messages = json.dumps(
                {
                    "author_advertisement": str(advertisement.author.id),
                    "renter": str(renter.id),
                    "advertisement": str(advertisement.id),
                }
            )

            send_message_to_author_queue(queue, json_messages)

            messages.success(
                request, f"Оплата прошла успешно! ID транзакции: {transaction.id}"
            )
        else:
            messages.error(request, f"Платёж не завершён (статус: {payment.status})")
    except Exception as e:
        logger.error(f"Ошибка при обработке платежа {payment_id}: {e}")
        messages.error(request, f"Ошибка проверки платежа: {e}")

    if "payment_id" in request.session:
        del request.session["payment_id"]
    if "rent_id" in request.session:
        del request.session["rent_id"]

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
        if data["event"] == "payment.succeeded":
            payment = data["object"]
        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "Invalid request"}, status=400)


def approve_ad(request):
    advertisements = Advertisement.objects.filter(is_approved=False)
    advertisemtnts = advertisements.filter(sold=False)

    if request.method == "POST":
        approved_ids = request.POST.getlist("approve_ad")

        Advertisement.objects.filter(id__in=approved_ids).update(is_approved=True)

        messages.success(request, f"Одобрено {len(approved_ids)} объявлений.")

        return redirect("advertisements")

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


def send_message_to_author_queue(queue_name, message):
    connection_params = pika.ConnectionParameters(host="localhost")
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()

    channel.queue_declare(queue=queue_name, durable=True)

    channel.basic_publish(
        exchange="",
        routing_key=queue_name,
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,
        ),
    )

    connection.close()


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

        context["image"] = advertisement.image_url
        context["title"] = advertisement.title
        context["category"] = advertisement.category
        context["author_id"] = advertisement.author
        context["description"] = advertisement.description

        context["comment_form"] = CommentForm()

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

        context = self.get_context_data()
        context["comment_form"] = form
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse("advertisement", kwargs={"pk": self.object.pk})


class AdvertisementCreateView(LoginRequiredMixin, CreateView):
    login_url = reverse_lazy("account_login")
    model = Advertisement
    form_class = AdvertisementForm

    def form_valid(self, form):
        form.instance.author = self.request.user
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
    form_class = AdvertisementForm

    def get_queryset(self):
        return Advertisement.objects.filter(author=self.request.user)

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

        advertisements = filter_advertisements()

        min_price = self.request.GET.get("min_price")
        max_price = self.request.GET.get("max_price")
        if min_price:
            try:
                advertisements = advertisements.filter(price__gte=float(min_price))
            except ValueError:
                pass
        if max_price:
            try:
                advertisements = advertisements.filter(price__lte=float(max_price))
            except ValueError:
                pass

        city = self.request.GET.get("city")
        if city:
            advertisements = advertisements.filter(location__city__iexact=city)

        paginator = Paginator(advertisements, settings.PAGE_ENTITY)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["advertisements"] = page_obj
        context["paginator"] = paginator
        context["page_obj"] = page_obj
        context["min_price"] = min_price
        context["max_price"] = max_price
        context["city"] = city

        context["cities"] = (
            Location.objects.values_list("city", flat=True)
            .distinct()
            .order_by("city")
        )

        return context


class RentListView(LoginRequiredMixin, ListView):
    login_url = reverse_lazy("account_login")
    template_name = os.path.join(TEMPLATE_DIR, "advertisement_rent_list.html")

    def get_queryset(self):
        return Rent.objects.for_user(self.request.user)


class SearchResultsView(ListView):
    model = Advertisement
    context_object_name = "advertisements"
    paginate_by = settings.PAGE_ENTITY

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
        context["advertisement"] = Advertisement.objects.get(pk=self.kwargs["ad_id"])
        return context

    def form_valid(self, form):
        ad_id = self.kwargs["ad_id"]
        renter_id = self.kwargs["author_id"]

        advertisement = Advertisement.objects.get(pk=ad_id)
        renter = User.objects.get(pk=renter_id)

        form.instance.advertisement = advertisement
        form.instance.renter = renter
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "buy_rent",
            kwargs={"ad_id": self.object.advertisement.id, "rent_id": self.object.id},
        )
