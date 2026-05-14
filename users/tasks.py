from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from users.models import User


@shared_task
def deactivate_inactive_users():
    check_date = timezone.now() - timedelta(days=30)
    User.objects.filter(last_login__lt=check_date, is_active=True).update(is_active=False)
    User.objects.filter(last_login__isnull=True, is_active=True).update(is_active=False)
