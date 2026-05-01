from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="OnlineClasses - LMS Platform",
        default_version="v1",
        description="""Данный проект представляет API для платформы онлайн-обучения.
                    Позволяет управлять курсами, уроками, пользователями и платежами.
                    OnlineClasses использует JWT (JSON Web Tokens) для аутентификации.
                    В проект добавлена постраничная пагинация, тесты, валидация на ссылки.""",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="itsmechernyi@gmail.com"),
        license=openapi.License(name="MIT License 2026 © [Chernyi Stas]"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("lms/", include("lms.urls", namespace="lms")),
    path("users/", include("users.urls", namespace="users")),
    path(
        "swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"
    ),
    path(
        "",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
