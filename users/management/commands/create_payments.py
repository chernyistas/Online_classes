from django.core.management import BaseCommand

from lms.models import Course, Lesson
from users.models import Payment, User


class Command(BaseCommand):
    help = "Create test payments"

    def handle(self, *args, **kwargs):

        try:
            user = User.objects.get(email="admin@admin.ru")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("Admin user not found! Run csu first."))
            return

        course = Course.objects.first()
        if not course:
            self.stdout.write(
                self.style.ERROR("No courses found! Create a course first.")
            )
            return

        lesson = Lesson.objects.first()
        if not lesson:
            self.stdout.write(
                self.style.ERROR("No lessons found! Create a lesson first.")
            )
            return

        payments_data = [
            {
                "user": user,
                "paid_course": course,
                "paid_lesson": None,
                "amount": 5000.00,
                "payment_method": "transfer",
            },
            {
                "user": user,
                "paid_course": None,
                "paid_lesson": lesson,
                "amount": 1500.00,
                "payment_method": "cash",
            },
        ]

        created_count = 0
        for data in payments_data:
            if data["paid_lesson"] is None and lesson is None:
                continue

            payment = Payment.objects.create(**data)
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Create payment: {payment.amount} руб. -"
                    f"{payment.paid_course if payment.paid_course else payment.paid_lesson}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {created_count} payments!")
        )
