from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "role", "clinic", "phone",
            "is_active", "date_joined",
        ]
        read_only_fields = ["id", "is_active", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "email", "password", "first_name", "last_name", "role", "phone"]

    def validate_role(self, value):
        # Self-registration is only open to patients; staff accounts are
        # provisioned by an admin via /api/users/.
        if value and value != User.Role.PATIENT:
            raise serializers.ValidationError("Self-registration is only available for patients.")
        return value or User.Role.PATIENT

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data["role"] = validated_data.get("role", User.Role.PATIENT)
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        return token
