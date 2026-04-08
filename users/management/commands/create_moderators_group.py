from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand


class Command(BaseCommand):
    """Создаёт группу модераторов"""

    help = "Create group of moderators"

    def handle(self, *args, **options):
        """Создает группу модераторов"""
        group, created = Group.objects.get_or_create(name="moderators")
        change_lesson = Permission.objects.get(codename="change_lesson")
        view_lesson = Permission.objects.get(codename="view_lesson")
        change_course = Permission.objects.get(codename="change_course")
        view_course = Permission.objects.get(codename="view_course")

        if created:
            group.permissions.add(change_lesson)
            group.permissions.add(view_lesson)
            group.permissions.add(change_course)
            group.permissions.add(view_course)
            group.save()
            self.stdout.write(
                self.style.SUCCESS("Successfully created group with permissions")
            )
        else:
            self.stdout.write(self.style.WARNING(f"Group - {group} already exist"))
