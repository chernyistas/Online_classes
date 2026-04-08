from django.db import models


class Course(models.Model):
    title = models.CharField(
        max_length=100, verbose_name="Название", help_text="Введите название"
    )
    preview = models.ImageField(
        upload_to="lms/preview",
        verbose_name="Превью",
        help_text="Загрузите превью",
        blank=True,
        null=True,
    )
    description = models.TextField(
        blank=True, null=True, verbose_name="Описание", help_text="Введите описание"
    )
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Владелец курса",
    )

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"


class Lesson(models.Model):
    title = models.CharField(
        max_length=100, verbose_name="Название", help_text="Введите название"
    )
    description = models.TextField(
        blank=True, null=True, verbose_name="Описание", help_text="Введите описание"
    )
    preview = models.ImageField(
        upload_to="lms/preview",
        blank=True,
        null=True,
        verbose_name="Картинка",
        help_text="Загрузите картинку",
    )
    video_link = models.URLField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Ссылка на  видео",
        help_text="Вставьте ссылку на видео",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name="Курс",
        help_text="Введите курс",
        related_name="lessons",
    )
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Владелец урока",
    )

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"


class Subscription(models.Model):

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="Курс")
    date_subscribed = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата подписки"
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        unique_together = ["user", "course"]
