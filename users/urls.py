from django.urls import path
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from users.apps import UsersConfig
from users.views import (PaymentListAPIView, UserCreateAPIView,
                         UserRetrieveAPIView, UserUpdateAPIView)

app_name = UsersConfig.name

urlpatterns = [
    path("<int:pk>/", UserRetrieveAPIView.as_view(), name="user-detail"),
    path("<int:pk>/update/", UserUpdateAPIView.as_view(), name="user_update"),
    path("payments/", PaymentListAPIView.as_view(), name="payment_list"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "register/",
        UserCreateAPIView.as_view(),
        name="register",
    ),
]
