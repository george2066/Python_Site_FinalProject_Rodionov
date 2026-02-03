import json
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from unittest.mock import patch, MagicMock

from advertisements.views import buy_advertisement
from users.models import User
from advertisements.models import Advertisement, Comment, Category
from django.utils import timezone

# Create your tests here.
class AdvertisementViewsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        # Создаём тестового пользователя
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="pass"
        )
        # Создаем категорию
        category = Category.objects.create(name="Test Category")
        # Создаём объявление
        self.ad = Advertisement.objects.create(
            title="Test Ad",
            description="Test description",
            price=100,
            category_id=1,  # укажите существующую категорию или создайте её в setUp
            author=self.user,
            image_url="http://example.com/image.jpg",
            is_approved=True,
            sold=False,
        )
        self.client.login(username="admin", password="pass")

    def test_advertisement_detail_view(self):
        url = reverse("advertisement", kwargs={"pk": self.ad.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ad.title)

    def test_create_comment(self):
        url = reverse("advertisement", kwargs={"pk": self.ad.pk})
        self.client.login(username="testuser", password="testpass")
        response = self.client.post(url, {"comment": "Test comment"})
        self.assertEqual(
            response.status_code, 302
        )  # редирект после успешного добавления
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
        response = self.client.post(
            url, json.dumps({"comment_id": comment.pk}), content_type="application/json"
        )
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
            location="City1",
            author=self.user,
        )
        ad2 = Advertisement.objects.create(
            title="Ad2",
            description="description2",
            price=2000,
            location="City2",
            author=self.user,
        )
        response = self.client.post(
            "/advertisements/approve/", data={"approve_ad": [str(ad1.id), str(ad2.id)]}
        )
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

    # Yookassa
    @patch("yookassa.Payment.create")
    @patch("yookassa.Configuration.account_id", new_callable=property)
    @patch("yookassa.Configuration.secret_key", new_callable=property)
    def test_buy_advertisement_success(
        self, mock_secret_key, mock_account_id, mock_create_payment
    ):
        # Настраиваем мок для Payment.create
        mock_payment = MagicMock()
        mock_payment.id = "payment_id_123"
        mock_payment.confirmation.confirmation_url = "http://testurl.com"
        mock_create_payment.return_value = mock_payment

        # Создаём запрос
        request = self.factory.get(reverse("buy_advertisement", args=[self.ad.id]))
        request.user = self.user
        request.session = {}

        # Вызываем функцию
        response = buy_advertisement(request, self.ad.id)

        # Проверяем редирект на URL оплаты
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "http://testurl.com")

        # Проверяем, что ID платежа сохранён в сессии
        self.assertEqual(request.session["payment_id"], "payment_id_123")
