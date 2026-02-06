import json
from datetime import datetime
from datetime import timedelta
from unittest.mock import MagicMock
from unittest.mock import patch

from django.contrib.messages import get_messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import Client
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse

from advertisements.models import Advertisement
from advertisements.models import Category
from advertisements.models import Comment
from advertisements.models import Location
from advertisements.models import Rent
from advertisements.models import Transaction
from advertisements.views import payment_success
from users.models import User


# Create your tests here.
class ViewsTestCase(TestCase):
    @classmethod
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        # Создаём тестового пользователя
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.admin = User.objects.create_superuser(username="admin", email="admin@example.com", password="pass")
        # Создаем категорию
        category = Category.objects.create(name="Test Category")
        # Создаём объявление
        self.location = Location.objects.create(
            city="Город",
            street="Улица",
            home="Дом",
            apartment="Квартира",
        )
        self.ad = Advertisement.objects.create(
            title="Test Ad",
            description="Test description",
            price=100,
            category_id=1,
            location=self.location,
            author=self.user,
            image_url="http://example.com/image.jpg",
            is_approved=True,
            sold=False,
        )
        self.rent = Rent.objects.create(
            advertisement=self.ad,
            renter=self.user,
            from_date=datetime(2023, 1, 1).date(),
            to_date=datetime(2023, 2, 2).date(),
            payed=False,
            create_at=datetime.now(),
            update_at=datetime.now(),
        )
        self.client.login(username="admin", password="pass")

    def add_middleware(self, request):
        session_middleware = SessionMiddleware(request)
        session_middleware.process_request(request)
        request.session.save()

        message_middleware = MessageMiddleware(request)
        message_middleware.process_request(request)

        return request

    def test_advertisement_detail_view(self):
        url = reverse("advertisement", kwargs={"pk": self.ad.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ad.title)

    def test_create_comment(self):
        url = reverse("advertisement", kwargs={"pk": self.ad.pk})
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(url, {"comment": "Test comment"})
        self.assertEqual(response.status_code, 302)  # редирект после успешного добавления
        self.assertTrue(Comment.objects.filter(comment="Test comment").exists())

    def test_edit_comment(self):
        comment = Comment.objects.create(
            user=self.user,
            advertisement=self.ad,
            comment="Old comment",
        )
        url = reverse("edit_comment")  # укажите правильный URL по вашему маршруту
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            url,
            json.dumps({"comment_id": comment.pk, "comment": "Updated comment"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.comment, "Updated comment")

    def test_delete_comment(self):
        comment = Comment.objects.create(
            user=self.user,
            advertisement=self.ad,
            comment="Comment to delete",
        )
        url = reverse("delete_comment")  # укажите правильный URL
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(url, json.dumps({"comment_id": comment.pk}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_search_view(self):
        response = self.client.get(reverse("search_results") + "?q=Test")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ad.title)

    def test_advertisement_list_view(self):
        response = self.client.get(reverse("advertisements"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ad.title)

    def test_advertisement_update(self):
        self.client.login(username="testuser", password="testpass")
        url = reverse("advertisement-update", kwargs={"pk": self.ad.pk})
        response = self.client.post(
            url,
            {
                "title": "Updated Title",
                "description": self.ad.description,
                "price": self.ad.price,
                "category": self.ad.category.id,
                "image_url": self.ad.image_url,
                "location": self.ad.location,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.ad.refresh_from_db()
        self.assertEqual(self.ad.title, "Updated Title")

    def test_advertisement_create(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(
            reverse("advertisement-add"),
            {
                "title": "New Ad",
                "description": "Desc",
                "price": 50,
                "category": 1,  # укажите существующую категорию
                "image_url": "http://example.com/image2.jpg",
                "location": "City",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Advertisement.objects.filter(title="New Ad").exists())

    def test_advertisement_delete(self):
        self.client.login(username="testuser", password="testpass")
        url = reverse("advertisement-delete", kwargs={"pk": self.ad.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Advertisement.objects.filter(pk=self.ad.pk).exists())

    def test_approve_ad(self):
        ad1 = Advertisement.objects.create(
            title="Ad1",
            description="description1",
            price=1000,
            location=self.location,
            author=self.user,
        )
        ad2 = Advertisement.objects.create(
            title="Ad2",
            description="description2",
            price=2000,
            location=self.location,
            author=self.user,
        )
        response = self.client.post("/advertisements/approve/", data={"approve_ad": [str(ad1.id), str(ad2.id)]})
        self.assertEqual(302, response.status_code)

        ad1.refresh_from_db()
        ad2.refresh_from_db()

        # Проверка, что они одобрены
        self.assertTrue(ad1.is_approved)
        self.assertTrue(ad2.is_approved)

        # Проверка сообщения (если есть)
        # Можно проверить сообщения через messages framework, например:
        messages_list = list(response.wsgi_request._messages)
        self.assertTrue(any("Одобрено" in str(msg) for msg in messages_list))

    @patch("yookassa.Payment.find_one")
    @patch("django.shortcuts.get_object_or_404")
    @patch("advertisements.views.send_message_to_author_queue")
    def test_payment_success_succeeded(self, mock_send_message, mock_get_object_or_404, mock_find_one):
        # Настройка mock Payment
        mock_payment = MagicMock()
        mock_payment.status = "succeeded"
        mock_payment.metadata = {
            "advertisement_id": self.ad.id,
            "rent_id": self.rent.id,
        }
        mock_find_one.return_value = mock_payment

        # Мокаем get_object_or_404 для объявления и аренды
        def get_obj_side_effect(model, id):
            if model == Advertisement:
                return self.ad
            elif model == Rent:
                return self.rent
            raise Exception("Unexpected model")

        mock_get_object_or_404.side_effect = get_obj_side_effect

        # Создаем запрос
        request = self.factory.get("/some-url/")
        request = self.add_middleware(request)

        # Устанавливаем сессионные данные
        request.session["payment_id"] = "test_payment_id"
        request.session["rent_id"] = self.rent.id
        request.session["advrtisement_id"] = self.ad.id

        # Вызов метода
        response = payment_success(request)

        # Проверка статуса
        self.assertEqual(response.status_code, 200)
        self.ad.refresh_from_db()

        # Проверка, что объявление помечено как sold
        self.assertTrue(self.ad.sold)
        self.rent.refresh_from_db()
        # Проверка, что аренда помечена как payed
        self.assertTrue(self.rent.payed)

        # Проверка, что транзакция создана
        self.assertTrue(Transaction.objects.filter(rent=self.rent).exists())

        # Проверка, что сообщение об успехе добавлено
        messages_list = list(get_messages(request))
        self.assertTrue(any("Оплата прошла успешно" in str(msg) for msg in messages_list))

        # Проверка, что отправлено сообщение в очередь
        mock_send_message.assert_called_once()

        # Проверка, что session очищена
        self.assertNotIn("payment_id", request.session)
        self.assertNotIn("rent_id", request.session)

    def test_overdue_field_calculation_positive(self):
        # Текущая дата
        today = datetime.now().date()

        # Создаем аренду с датой окончания в прошлом — overdue должно стать True
        rent_past = Rent.objects.create(
            advertisement=self.ad,
            renter=self.user,
            from_date=today.replace(day=1),  # произвольно
            to_date=today.replace(day=1) - timedelta(days=1),  # вчера
        )
        rent_past.refresh_from_db()
        self.assertTrue(rent_past.overdue, "Поле overdue должно быть True для прошедших дат")

    def test_overdue_field_calculation_negative(self):
        today = datetime.now().date()
        # Создаем аренду с датой окончания в будущем — overdue должно стать False
        future_date = today + timedelta(days=10)
        rent_future = Rent.objects.create(
            advertisement=self.ad,
            renter=self.user,
            from_date=today,
            to_date=future_date,
        )
        rent_future.refresh_from_db()
        self.assertFalse(rent_future.overdue, "Поле overdue должно быть False для будущих дат")

    @patch("yookassa.Payment.find_one")
    def test_exception_handling(self, mock_find_one):
        mock_find_one.side_effect = Exception("Ошибка API")
        request = self.factory.get("/some-url/")
        request = self.add_middleware(request)
        request.session["payment_id"] = "test_payment_id"
        request.session["rent_id"] = self.rent.id
        request.session["advrtisement_id"] = self.ad.id

        response = payment_success(request)

        self.assertEqual(response.status_code, 200)
        messages_list = list(get_messages(request))
        self.assertTrue(any("Ошибка проверки платежа" in str(msg) for msg in messages_list))
        # Проверка, что объекты не обновлены
        self.ad.refresh_from_db()
        self.rent.refresh_from_db()
        self.assertFalse(self.ad.sold)
        self.assertFalse(self.rent.payed)
