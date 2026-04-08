from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from lms.models import Course

from .models import Payment, User


class UserProfileTestCase(APITestCase):
    """Тесты для пользователя"""

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        self.user1 = User.objects.create_user(
            email="user1@test.com", password="User1pass123"
        )
        self.user2 = User.objects.create_user(
            email="user2@test.com", password="User2pass123"
        )
        self.client.force_authenticate(user=self.user1)

        self.list_url = reverse("lms:lesson_list")
        self.profile_url = reverse("users:user_detail", args=[self.user2.pk])
        self.update_url = reverse("users:user_update", args=[self.user2.pk])

    def test_own_profile_has_payments(self):
        """Свой профиль - есть поле payments"""
        url = reverse("users:user_detail", args=[self.user1.pk])
        response = self.client.get(url)
        self.assertIn("payments", response.data)

    def other_profile_has_not_payments(self):
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
        self.user = User.objects.create_user(
            email="user@test.com", password="Userpass123"
        )
        self.course = Course.objects.create(title="Course", owner=self.user)
        Payment.objects.create(
            user=self.user, paid_course=self.course, amount=1000, payment_method="cash"
        )
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
