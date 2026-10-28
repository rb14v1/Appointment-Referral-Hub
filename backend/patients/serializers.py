from rest_framework import serializers

from accounts.serializers import UserSerializer
from patients.models import Patient


class PatientSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source="user", read_only=True)

    class Meta:
        model = Patient
        fields = ["id", "user", "user_detail", "date_of_birth", "primary_clinic", "emergency_contact"]
