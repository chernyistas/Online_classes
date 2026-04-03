from django.urls import path

from users.apps import UsersConfig
from users.views import PaymentListAPIView, UserRetrieveAPIView, UserUpdateAPIView

app_name = UsersConfig.name

urlpatterns = [
    path("<int:pk>/", UserRetrieveAPIView.as_view(), name="user-detail"),
    path("<int:pk>/update/", UserUpdateAPIView.as_view(), name="user_update"),
    path("payments/", PaymentListAPIView.as_view(), name="payment_list"),
]
