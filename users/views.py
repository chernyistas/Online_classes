from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.models import Payment, User
from users.permissions import IsOwner
from users.serializers import PaymentSerializer, UserPublicSerializer, UserRegisterSerializer, UserSerializer
from users.services import (
    create_checkout_session,
    create_stripe_price,
    create_stripe_product,
    retrieve_checkout_session,
)


class UserUpdateAPIView(UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwner]


class UserRetrieveAPIView(RetrieveAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        user = self.get_object()
        if self.request.user == user:
            return UserSerializer
        return UserPublicSerializer


class PaymentListAPIView(ListAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["payment_method", "paid_course", "paid_lesson"]
    ordering_fields = ["payment_date"]


class UserCreateAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]


class PaymentCreateAPIView(CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        payment = serializer.save(user=self.request.user, status="pending")
        course = payment.paid_course
        lesson = payment.paid_lesson

        if not course and not lesson:
            raise ValidationError("Укажите course_id или lesson_id")

        if course and lesson:
            raise ValidationError("Укажите только один параметр")

        obj = course if course else lesson
        product_name = obj.title
        amount = float(payment.amount)
        if amount <= 0:
            raise ValidationError("Сумма оплаты должна быть больше 0")
        try:
            # 1. Создаем продукт в Stripe
            product = create_stripe_product(product_name, product_name)

            # 2. Создаем цену
            price = create_stripe_price(product.id, amount)

            # 3. Создаем сессию
            success_url = "http://localhost:8000/lms/"
            cancel_url = "http://localhost:8000/lms/"
            session_id, payment_url = create_checkout_session(price.id, success_url, cancel_url)
        except Exception as e:
            payment.delete()
            raise ValidationError(f"Ошибка при создании платежа в Stripe: {str(e)}")
        # 4. Сохраняем данные
        payment.stripe_session_id = session_id
        payment.stripe_payment_url = payment_url
        payment.save()


class PaymentRetrieveAPIView(RetrieveAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsOwner]

    def get(self, request, *args, **kwargs):
        payment = self.get_object()
        session_id = payment.stripe_session_id

        if not session_id:
            return Response(
                {"error": "У этого платежа нет сессии Stripe"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session = retrieve_checkout_session(session_id)

        stripe_status = session.payment_status

        if stripe_status == "paid":
            payment.status = "paid"
        elif stripe_status == "unpaid":
            payment.status = "pending"

        payment.save()

        return Response(
            {
                "payment_id": payment.id,
                "status": payment.status,
                "stripe_status": stripe_status,
            }
        )
