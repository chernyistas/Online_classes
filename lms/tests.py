from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from lms.models import Course, Lesson, Subscription
from users.models import User


class LessonTestCase(APITestCase):
    """Тесты для уроков."""

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        self.owner = User.objects.create_user(email="owner@test.com", password="Ownerpass123")
        self.moder = User.objects.create_user(email="moder@test.com", password="Moderpass123")
        self.user = User.objects.create_user(email="user@test.com", password="Userpass123")
        group, created = Group.objects.get_or_create(name="moderators")
        self.moder.groups.add(group)

        self.course = Course.objects.create(title="Тестовый курс", owner=self.owner)

        self.lesson = Lesson.objects.create(title="Тестовый урок", owner=self.owner, course=self.course)

        self.client.force_authenticate(user=self.owner)

        self.list_url = reverse("lms:lesson_list")
        self.retrieve_url = reverse("lms:lesson_retrieve", args=[self.lesson.pk])
        self.update_url = reverse("lms:lesson_update", args=[self.lesson.pk])
        self.delete_url = reverse("lms:lesson_delete", args=[self.lesson.pk])
        self.create_url = reverse("lms:lesson_create")

    def test_create_lesson(self):
        """Тест на создание урока."""

        data = {
            "title": "Новый тестовый урок",
            "course": self.course.pk,
        }

        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.all().count(), 2)
        self.assertIn("тестовый урок", str(response.data["title"]))

    def test_create_lesson_unauthenticated(self):
        """Тест на создание урока не авторизованным пользователем."""

        self.client.force_authenticate(user=None)
        data = {"title": "Попытка создания урока неавторизованным пользователем"}
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Lesson.objects.all().count(), 1)

    def test_list_lesson(self):
        """Тест на просмотр списка уроков"""
        response = self.client.get(self.list_url)
        data = response.json()
        result = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": self.lesson.pk,
                    "video_link": None,
                    "title": self.lesson.title,
                    "description": None,
                    "preview": None,
                    "course": self.course.pk,
                    "owner": self.owner.pk,
                }
            ],
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data, result)

    def test_update_lesson(self):
        """Тест на обновление урока"""
        data = {"title": "Новое название", "course": self.course.pk}
        response = self.client.patch(self.update_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(response.data["title"], self.lesson.title)

    def test_delete_lesson(self):
        """Тест на удаление урока"""
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lesson.objects.all().count(), 0)

    def test_moder_can_update_any_lesson(self):
        """Тест на права модератора"""
        self.client.force_authenticate(user=self.moder)
        data = {"title": "Изменил модератор"}
        response = self.client.patch(self.update_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertIn("Изменил модератор", str(response.data["title"]))

    def test_user_cannot_update_other_lesson(self):
        """Тест на права обычного пользователя - не владельца"""
        self.client.force_authenticate(user=self.user)
        data = {"title": "попытка взлома", "course": self.course.pk}
        response = self.client.patch(self.update_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SubscriptionTestCase(APITestCase):
    """Тесты для подписки"""

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        self.user = User.objects.create_user(email="user@test.com", password="Userpass123")
        self.client.force_authenticate(user=self.user)
        self.course = Course.objects.create(title="Курс для подписки", owner=self.user)
        self.url = reverse("lms:subscription")

    def test_subscribe_to_course(self):
        """Тест подписки на курс"""
        response = self.client.post(self.url, {"course_id": self.course.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "подписка добавлена")
        self.assertTrue(Subscription.objects.filter(user=self.user, course=self.course).exists())

    def test_unsubscribe_from_course(self):
        """Тест отписки от курса"""
        Subscription.objects.create(user=self.user, course=self.course)
        response = self.client.post(self.url, {"course_id": self.course.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "подписка удалена")
        self.assertFalse(Subscription.objects.filter(user=self.user, course=self.course).exists())

    def test_subscribe_missing_course_id(self):
        """Тест: course_id не передан"""
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_subscribe_nonexistent_course(self):
        """Тест на не существующий курс"""
        response = self.client.post(self.url, {"course_id": 555})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CourseTestCase(APITestCase):
    """Тесты для курсов"""

    def setUp(self):
        """Подготовка данных перед каждым тестом"""
        self.owner = User.objects.create_user(email="owner@test.com", password="Ownerpass123")
        self.moder = User.objects.create_user(email="moder@test.com", password="Moderpass123")
        self.user = User.objects.create_user(email="user@test.com", password="Userpass123")
        self.course = Course.objects.create(title="Тестовый курс", owner=self.owner)
        self.client.force_authenticate(user=self.owner)
        group, created = Group.objects.get_or_create(name="moderators")
        self.moder.groups.add(group)
        self.list_url = reverse("lms:course-list")
        self.retrieve_url = reverse("lms:course-detail", args=[self.course.pk])
        self.update_url = reverse("lms:course-detail", args=[self.course.pk])
        self.delete_url = reverse("lms:course-detail", args=[self.course.pk])
        self.create_url = reverse("lms:course-list")

    def test_create_course(self):
        """Тест на создание курас владельцем"""
        data = {"title": "Новый курс"}
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.all().count(), 2)

    def test_create_course_by_moder(self):
        """Тест на создание курса модератором"""
        self.client.force_authenticate(user=self.moder)
        data = {
            "title": "Новый курс",
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Course.objects.count(), 1)

    def test_list_courses(self):
        """Тест на то, что владелец видит свои"""
        Course.objects.create(title="Тестовый курс от user", owner=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Тестовый курс")

    def test_update_course_by_owner(self):
        """Владелец может обновить свой курс"""
        data = {"title": "Новое название курса"}
        response = self.client.patch(self.update_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Новое название курса", str(response.data["title"]))

    def test_update_course_by_moder(self):
        """Модератор может обновить любой курс"""
        self.client.force_authenticate(user=self.moder)
        data = {"title": "Модер поменял название"}
        response = self.client.patch(self.update_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Модер поменял название", str(response.data["title"]))

    def test_update_course_other_user(self):
        """Пользователь не может обновить не свой курс"""
        self.client.force_authenticate(user=self.user)
        data = {"title": "Попытка взлома"}
        response = self.client.patch(self.update_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_course_by_owner(self):
        """Владелец может удалить свой курс"""

        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Course.objects.all().count(), 0)

    def test_delete_course_by_moder(self):
        """Модератор не может удалить курс"""
        self.client.force_authenticate(user=self.moder)

        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
