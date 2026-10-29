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
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="pass"
        )
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
        self.assertEqual(response.status_code, 302)
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
                "city": self.ad.location.city,
                "street": self.ad.location.street,
                "home": self.ad.location.home,
                "apartment": self.ad.location.apartment,
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
                "category": 1,
                "image_url": "http://example.com/image2.jpg",
                "city": "TestCity",
                "street": "TestStreet",
                "home": "1",
                "apartment": "10",
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
        response = self.client.post(
            "/advertisements/approve/", data={"approve_ad": [str(ad1.id), str(ad2.id)]}
        )
        self.assertEqual(302, response.status_code)

        ad1.refresh_from_db()
        ad2.refresh_from_db()

        self.assertTrue(ad1.is_approved)
        self.assertTrue(ad2.is_approved)

        messages_list = list(response.wsgi_request._messages)
        self.assertTrue(any("Одобрено" in str(msg) for msg in messages_list))

    @patch("yookassa.Payment.find_one")
    @patch("django.shortcuts.get_object_or_404")
    @patch("advertisements.views.send_message_to_author_queue")
    def test_payment_success_succeeded(
        self, mock_send_message, mock_get_object_or_404, mock_find_one
    ):
        mock_payment = MagicMock()
        mock_payment.status = "succeeded"
        mock_payment.metadata = {
            "advertisement_id": self.ad.id,
            "rent_id": self.rent.id,
        }
        mock_find_one.return_value = mock_payment

        def get_obj_side_effect(model, id):
            if model == Advertisement:
                return self.ad
            elif model == Rent:
                return self.rent
            raise Exception("Unexpected model")

        mock_get_object_or_404.side_effect = get_obj_side_effect

        request = self.factory.get("/some-url/")
        request = self.add_middleware(request)

        request.session["payment_id"] = "test_payment_id"
        request.session["rent_id"] = self.rent.id
        request.session["advrtisement_id"] = self.ad.id

        response = payment_success(request)

        self.assertEqual(response.status_code, 200)
        self.ad.refresh_from_db()

        self.assertTrue(self.ad.sold)
        self.rent.refresh_from_db()
        self.assertTrue(self.rent.payed)

        self.assertTrue(Transaction.objects.filter(rent=self.rent).exists())

        messages_list = list(get_messages(request))
        self.assertTrue(
            any("Оплата прошла успешно" in str(msg) for msg in messages_list)
        )

        mock_send_message.assert_called_once()

        self.assertNotIn("payment_id", request.session)
        self.assertNotIn("rent_id", request.session)

    def test_overdue_field_calculation_positive(self):
        today = datetime.now().date()

        rent_past = Rent.objects.create(
            advertisement=self.ad,
            renter=self.user,
            from_date=today.replace(day=1),
            to_date=today.replace(day=1) - timedelta(days=1),
        )
        rent_past.refresh_from_db()
        self.assertTrue(rent_past.overdue)

    def test_overdue_field_calculation_negative(self):
        today = datetime.now().date()
        future_date = today + timedelta(days=10)
        rent_future = Rent.objects.create(
            advertisement=self.ad,
            renter=self.user,
            from_date=today,
            to_date=future_date,
        )
        rent_future.refresh_from_db()
        self.assertFalse(rent_future.overdue)

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
        self.assertTrue(
            any("Ошибка проверки платежа" in str(msg) for msg in messages_list)
        )
        self.ad.refresh_from_db()
        self.rent.refresh_from_db()
        self.assertFalse(self.ad.sold)
        self.assertFalse(self.rent.payed)

    def setUpFilters(self):
        self.location_msk = Location.objects.create(
            city="Москва", street="Ленина", home="1"
        )
        self.location_spb = Location.objects.create(
            city="Санкт-Петербург", street="Пушкина", home="2"
        )
        self.location_kazan = Location.objects.create(
            city="Казань", street="Батурина", home="3"
        )

        self.ad_expensive = Advertisement.objects.create(
            title="Expensive Ad",
            description="Expensive",
            price=5000,
            category=self.ad.category,
            location=self.location_msk,
            author=self.user,
            is_approved=True,
            sold=False,
        )
        self.ad_medium = Advertisement.objects.create(
            title="Medium Ad",
            description="Medium price",
            price=1000,
            category=self.ad.category,
            location=self.location_spb,
            author=self.user,
            is_approved=True,
            sold=False,
        )
        self.ad_cheap = Advertisement.objects.create(
            title="Cheap Ad",
            description="Cheap",
            price=100,
            category=self.ad.category,
            location=self.location_kazan,
            author=self.user,
            is_approved=True,
            sold=False,
        )

    def test_filter_by_price_min(self):
        self.setUpFilters()
        response = self.client.get(reverse("advertisements"), {"min_price": "900"})
        self.assertEqual(response.status_code, 200)
        ads_in_context = list(response.context["advertisements"])
        ad_titles = [ad.title for ad in ads_in_context]
        self.assertIn("Medium Ad", ad_titles)
        self.assertIn("Expensive Ad", ad_titles)
        self.assertNotIn("Cheap Ad", ad_titles)

    def test_filter_by_price_max(self):
        self.setUpFilters()
        response = self.client.get(reverse("advertisements"), {"max_price": "1000"})
        self.assertEqual(response.status_code, 200)
        ads_in_context = list(response.context["advertisements"])
        ad_titles = [ad.title for ad in ads_in_context]
        self.assertIn("Test Ad", ad_titles)
        self.assertIn("Cheap Ad", ad_titles)
        self.assertIn("Medium Ad", ad_titles)
        self.assertNotIn("Expensive Ad", ad_titles)

    def test_filter_by_price_min_and_max(self):
        self.setUpFilters()
        response = self.client.get(
            reverse("advertisements"), {"min_price": "50", "max_price": "2000"}
        )
        self.assertEqual(response.status_code, 200)
        ads_in_context = list(response.context["advertisements"])
        ad_titles = [ad.title for ad in ads_in_context]
        self.assertIn("Test Ad", ad_titles)
        self.assertIn("Cheap Ad", ad_titles)
        self.assertIn("Medium Ad", ad_titles)
        self.assertNotIn("Expensive Ad", ad_titles)

    def test_filter_by_city(self):
        self.setUpFilters()
        response = self.client.get(reverse("advertisements"), {"city": "Москва"})
        self.assertEqual(response.status_code, 200)
        ads_in_context = list(response.context["advertisements"])
        ad_titles = [ad.title for ad in ads_in_context]
        self.assertIn("Expensive Ad", ad_titles)
        self.assertNotIn("Test Ad", ad_titles)
        self.assertNotIn("Medium Ad", ad_titles)

    def test_filter_by_city_case_insensitive(self):
        self.setUpFilters()
        response = self.client.get(reverse("advertisements"), {"city": "Москва"})
        self.assertEqual(response.status_code, 200)
        ads_in_context = list(response.context["advertisements"])
        ad_titles = [ad.title for ad in ads_in_context]
        self.assertIn("Expensive Ad", ad_titles)
        self.assertNotIn("Test Ad", ad_titles)

    def test_filter_by_city_not_exists(self):
        self.setUpFilters()
        response = self.client.get(reverse("advertisements"), {"city": "Владивосток"})
        self.assertEqual(response.status_code, 200)
        ads_in_context = list(response.context["advertisements"])
        self.assertEqual(len(ads_in_context), 0)

    def test_combined_filters_price_and_city(self):
        self.setUpFilters()
        response = self.client.get(
            reverse("advertisements"),
            {"min_price": "500", "city": "Санкт-Петербург"},
        )
        self.assertEqual(response.status_code, 200)
        ads_in_context = list(response.context["advertisements"])
        ad_titles = [ad.title for ad in ads_in_context]
        self.assertIn("Medium Ad", ad_titles)
        self.assertNotIn("Expensive Ad", ad_titles)
        self.assertNotIn("Test Ad", ad_titles)

    def test_filters_preserved_in_pagination(self):
        self.setUpFilters()
        response = self.client.get(
            reverse("advertisements"), {"min_price": "100", "city": "Москва"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["min_price"], "100")
        self.assertEqual(response.context["city"], "Москва")

    def test_cities_list_in_context(self):
        self.setUpFilters()
        response = self.client.get(reverse("advertisements"))
        self.assertEqual(response.status_code, 200)
        cities = list(response.context["cities"])
        self.assertIn("Москва", cities)
        self.assertIn("Санкт-Петербург", cities)
        self.assertIn("Казань", cities)

    def test_no_filters_returns_all(self):
        self.setUpFilters()
        response = self.client.get(reverse("advertisements"))
        self.assertEqual(response.status_code, 200)
        ads_in_context = list(response.context["advertisements"])
        self.assertGreaterEqual(len(ads_in_context), 4)
