from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from lms.models import Course, Lesson

from .models import Payment, User


class UserProfileTestCase(APITestCase):
    """Тесты для пользователя"""

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        self.user1 = User.objects.create_user(email="user1@test.com", password="User1pass123")
        self.user2 = User.objects.create_user(email="user2@test.com", password="User2pass123")
        self.client.force_authenticate(user=self.user1)

        self.list_url = reverse("lms:lesson_list")
        self.profile_url = reverse("users:user_detail", args=[self.user2.pk])
        self.update_url = reverse("users:user_update", args=[self.user2.pk])

    def test_own_profile_has_payments(self):
        """Свой профиль - есть поле payments"""
        url = reverse("users:user_detail", args=[self.user1.pk])
        response = self.client.get(url)
        self.assertIn("payments", response.data)

    def test_other_profile_has_not_payments(self):
        """Чужой профиль - нет поля payments"""
        response = self.client.get(self.profile_url)
        self.assertNotIn("payments", response.data)

    def test_update_own_profile(self):
        """Можно обновить свой профиль"""
        url = reverse("users:user_update", args=[self.user1.pk])
        response = self.client.patch(url, {"city": "Moscow"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Moscow", str(response.data["city"]))

    def test_update_other_profile_forbidden(self):
        """Нельзя обновить чужой профиль"""
        response = self.client.patch(self.update_url, {"city": "Moscow"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PaymentTestCase(APITestCase):
    """Тесты для платежей"""

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        self.user = User.objects.create_user(email="user@test.com", password="Userpass123")
        self.course = Course.objects.create(title="Course", owner=self.user)
        Payment.objects.create(user=self.user, paid_course=self.course, amount=1000, payment_method="cash")
        self.client.force_authenticate(user=self.user)
        self.url = reverse("users:payment_list")

    def test_payment_list(self):
        """Тест на список платежей"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Payment.objects.all().count(), 1)

    def test_payment_filter_by_method(self):
        response = self.client.get(self.url, {"payment_method": "cash"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PaymentCreateTestCase(APITestCase):
    """Тесты для создания платежей через Stripe"""

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        self.user = User.objects.create_user(email="user@test.com", password="Userpass123")
        self.course = Course.objects.create(title="Курс по Python", owner=self.user)
        self.url = reverse("users:payments-create")
        self.client.force_authenticate(user=self.user)

        self.valid_data = {
            "paid_course": self.course.id,
            "amount": "1000",
            "payment_method": "transfer",
        }

    @patch("users.services.stripe.Product.create")
    @patch("users.services.stripe.Price.create")
    @patch("users.services.stripe.checkout.Session.create")
    def test_create_payment_success(self, mock_session, mock_price, mock_product):
        """Тест на успешное создание платежа за курс с моками."""
        mock_product.return_value.id = "prod_test_123"
        mock_price.return_value.id = "price_test_456"
        mock_session.return_value.id = "sess_test_789"
        mock_session.return_value.url = "https://checkout.stripe.com/test"

        response = self.client.post(self.url, self.valid_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.count(), 1)

        payment = Payment.objects.first()
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.paid_course, self.course)
        self.assertEqual(float(payment.amount), 1000.00)
        self.assertEqual(payment.status, "pending")
        self.assertEqual(payment.stripe_session_id, "sess_test_789")
        self.assertEqual(payment.stripe_payment_url, "https://checkout.stripe.com/test")

    def test_create_payment_unauthenticated(self):
        """Тест: Неавторизованный пользователь НЕ может создать платеж"""

        self.client.force_authenticate(user=None)
        response = self.client.post(self.url, self.valid_data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Payment.objects.count(), 0)

    def test_create_payment_missing_course_or_lesson(self):
        """Тест: Ошибка если не указан ни курс, ни урок"""

        invalid_data = {"amount": "10000", "payment_method": "transfer"}

        response = self.client.post(self.url, invalid_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Укажите course_id или lesson_id", str(response.data))

    def test_create_payment_both_course_and_lesson(self):
        """Тест на указание одновременно и курса и урока"""

        lesson = Lesson.objects.create(title="Урок 1", course=self.course, owner=self.user)

        invalid_data = {
            "paid_course": self.course.id,
            "paid_lesson": lesson.id,
            "amount": "1000.00",
            "payment_method": "transfer",
        }

        response = self.client.post(self.url, invalid_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Укажите только один параметр", str(response.data))


class PaymentStatusTestCase(APITestCase):
    """Тесты для проверки статуса платежа"""

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        self.owner = User.objects.create_user(email="owner@test.com", password="Ownerpass123")
        self.other_user = User.objects.create_user(email="other@test.com", password="Otherpass123")
        self.course = Course.objects.create(title="Тестовый курс", owner=self.owner)
        self.payment = Payment.objects.create(
            user=self.owner,
            paid_course=self.course,
            amount=1000.00,
            payment_method="transfer",
            status="pending",
            stripe_session_id="sess_test_123",
        )
        self.client.force_authenticate(user=self.owner)
        self.url = reverse("users:payment-status", args=[self.payment.id])

    @patch("users.services.stripe.checkout.Session.retrieve")
    def test_owner_can_view_status(self, mock_retrieve):
        """Тест на то, что владелец платежа может проверить статус"""

        mock_session = type("MockSession", (), {"payment_status": "paid"})()
        mock_retrieve.return_value = mock_session
        self.client.force_authenticate(user=self.owner)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("payment_id", response.data)
        self.assertIn("status", response.data)
        self.assertIn("stripe_status", response.data)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "paid")

    def test_other_user_cannot_view_status(self):
        """Тест на то, что чужой пользователь НЕ может проверить статус"""

        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "pending")

    def test_unauthenticated_cannot_view_status(self):
        """Тест на то, что неавторизованный пользователь НЕ может проверить статус"""

        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_payment_without_session_id(self):
        """Тест на то, что платеж без stripe_session_id возвращает ошибку"""

        payment_no_session = Payment.objects.create(
            user=self.owner,
            paid_course=self.course,
            amount=500.00,
            payment_method="cash",
            status="pending",
            stripe_session_id=None,
        )

        url = reverse("users:payment-status", args=[payment_no_session.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("нет сессии Stripe", str(response.data["error"]))
