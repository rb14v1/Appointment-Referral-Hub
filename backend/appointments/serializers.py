from rest_framework import serializers

from appointments.models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    provider_name = serializers.SerializerMethodField()
    clinic_name = serializers.CharField(source="clinic.name", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id", "patient", "provider", "clinic", "start_time", "end_time",
            "status", "reason", "created_by", "referral", "created_at",
            "updated_at", "patient_name", "provider_name", "clinic_name",
        ]
        read_only_fields = ["id", "status", "end_time", "created_by", "created_at", "updated_at"]

    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name() or obj.patient.user.email

    def get_provider_name(self, obj):
        return obj.provider.user.get_full_name() or obj.provider.user.email


class BookAppointmentSerializer(serializers.Serializer):
    patient = serializers.IntegerField()
    provider = serializers.IntegerField()
    clinic = serializers.IntegerField()
    start_time = serializers.DateTimeField()
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    referral = serializers.IntegerField(required=False, allow_null=True)


class CancelAppointmentSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")
