from django.core.management import BaseCommand

from users.models import User


class Command(BaseCommand):
    help = "Create superuser"

    def handle(self, *args, **kwargs):
        user = User.objects.create(email="admin@test.ru")
        user.set_password("password")
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()

        self.stdout.write(self.style.SUCCESS(f"Successfully created admin user with email {user.email}!"))
