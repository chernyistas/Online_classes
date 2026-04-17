from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from lms.models import Course, Lesson


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
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
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


PAYMENT_METHODS = [("cash", "наличные"), ("transfer", "перевод")]
STRIPE_STATUS = [
    ("pending", "в ожидании"),
    ("paid", "оплачено"),
    ("failed", "отказано"),
]


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
    stripe_session_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="id сессии"
    )
    stripe_payment_url = models.URLField(
        max_length=500, blank=True, null=True, verbose_name="ссылка платежа"
    )
    status = models.CharField(
        max_length=20,
        choices=STRIPE_STATUS,
        default="pending",
        verbose_name="статус платежа",
    )

    class Meta:
        verbose_name = "платеж"
        verbose_name_plural = "платежи"
