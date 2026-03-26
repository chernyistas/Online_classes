from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models

from lms.models import Lesson, Course


class User(AbstractBaseUser):
    username = None

    email = models.EmailField(
        unique=True, verbose_name="Почта", help_text="Введите почту"
    )
    phone = models.CharField(
        max_length=35,
        verbose_name="Телефон",
        help_text="Введите телефон",
        blank=True,
        null=True,
    )
    avatar = models.ImageField(
        upload_to="users/avatar",
        verbose_name="Аватар",
        help_text="Загрузите аватар",
        blank=True,
        null=True,
    )
    city = models.CharField(
        max_length=100,
        verbose_name="Город",
        help_text="Введите город",
        blank=True,
        null=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


PAYMENT_METHODS = [("cash", "наличные"), ("transfer", "перевод")]


class Payment(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="пользователь"
    )
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата оплаты")
    paid_course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name="Курс оплачен",
        blank=True,
        null=True,
    )
    paid_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        verbose_name="Урок оплачен",
        blank=True,
        null=True,
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Сумма оплаты"
    )
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHODS,
        default="transfer",
        verbose_name="метод оплаты",
    )

    class Meta:
        verbose_name = "платеж"
        verbose_name_plural = "платежи"
