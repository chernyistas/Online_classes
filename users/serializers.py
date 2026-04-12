from rest_framework.serializers import ModelSerializer

from users.models import Payment, User


class PaymentSerializer(ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ["user", "stripe_session_id", "stripe_payment_url", "status"]


class UserSerializer(ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True, source="payment_set")

    class Meta:
        model = User
        exclude = ["password"]


class UserPublicSerializer(ModelSerializer):
    class Meta:
        model = User
        exclude = ["password"]


class UserRegisterSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "phone", "avatar", "city", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = True
        user.save()
        return user
