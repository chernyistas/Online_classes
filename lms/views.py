from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import (CreateAPIView, DestroyAPIView,
                                     ListAPIView, RetrieveAPIView,
                                     UpdateAPIView)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from lms.models import Course, Lesson, Subscription
from lms.paginators import StandardResultsSetPagination
from lms.serializers import CourseSerializer, LessonSerializer
from lms.tasks import send_course_update_email_notification
from users.permissions import IsModer, IsOwner


class CourseViewSet(ModelViewSet):
    queryset = Course.objects.all().order_by("id")
    serializer_class = CourseSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user

        # Неавторизованный пользователь видит все курсы
        if not user.is_authenticated:
            return Course.objects.all()

        # Модератор видит все курсы
        if user.groups.filter(name="moderators").exists():
            return Course.objects.all()

        # Обычный пользователь видит только свои курсы
        return Course.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = [AllowAny]
        elif self.action == "create":
            self.permission_classes = [IsAuthenticated, ~IsModer]
        elif self.action in ["update", "partial_update"]:
            self.permission_classes = [IsAuthenticated, IsModer | IsOwner]
        elif self.action == "destroy":
            self.permission_classes = [IsAuthenticated, IsOwner]

        return [permission() for permission in self.permission_classes]

    def update(self, request, *args, **kwargs):
        last_update = self.get_object().last_updated
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:
            new_course = self.get_object()
            now = timezone.now()

            if now - last_update > timedelta(hours=4):
                send_course_update_email_notification.delay(new_course.id)

        return response

    def partial_update(self, request, *args, **kwargs):
        last_update = self.get_object().last_updated
        response = super().partial_update(request, *args, **kwargs)
        if response.status_code == 200:
            new_course = self.get_object()
            now = timezone.now()

            if now - last_update > timedelta(hours=4):
                send_course_update_email_notification.delay(new_course.id)

        return response


class LessonListAPIView(ListAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name="moderators").exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)


class LessonRetrieveAPIView(RetrieveAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsModer | IsOwner]


class LessonUpdateAPIView(UpdateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsModer | IsOwner]

    def perform_update(self, serializer):
        lesson = self.get_object()
        course = lesson.course
        last_update = course.last_updated
        super().perform_update(serializer)

        now = timezone.now()
        if now - last_update > timedelta(hours=4):
            send_course_update_email_notification.delay(course.id)


class LessonCreateAPIView(CreateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, ~IsModer]  # type: ignore

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonDestroyAPIView(DestroyAPIView):
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated, IsOwner]


class SubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        course_id = request.data.get("course_id")

        if not course_id:
            return Response({"error": "course_id"}, status=status.HTTP_400_BAD_REQUEST)

        course = get_object_or_404(Course, id=course_id)

        subscription = Subscription.objects.filter(user=user, course=course)

        if subscription.exists():
            subscription.delete()
            message = "подписка удалена"
        else:
            Subscription.objects.create(user=user, course=course)
            message = "подписка добавлена"

        return Response({"message": message}, status=status.HTTP_200_OK)
