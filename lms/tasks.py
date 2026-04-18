from celery import shared_task
from django.core.mail import send_mail

from config.settings import EMAIL_HOST_USER
from lms.models import Subscription


@shared_task
def send_course_update_email_notification(course_id):
    """Отправляет сообщение об обновлении материалов курса"""
    subscriptions = Subscription.objects.filter(course_id=course_id)
    for subscription in subscriptions:
        user_email = subscription.user.email
        send_mail(
            "Обновление",
            f"Материалы курса {subscription.course.title} обновлены!",
            EMAIL_HOST_USER,
            [user_email],
        )
