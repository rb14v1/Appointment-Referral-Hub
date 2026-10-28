from rest_framework import serializers

from referrals.models import Referral


class ReferralSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = Referral
        fields = [
            "id", "patient", "referring_clinic", "referring_provider",
            "receiving_clinic", "receiving_provider", "reason", "urgency",
            "status", "notes", "created_by", "created_at", "resolved_at",
            "patient_name",
        ]
        read_only_fields = ["id", "status", "created_by", "created_at", "resolved_at"]

    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name() or obj.patient.user.email


class ReferralAcceptSerializer(serializers.Serializer):
    receiving_provider = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class ReferralRejectSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)


class ReferralScheduleSerializer(serializers.Serializer):
    provider = serializers.IntegerField()
    start_time = serializers.DateTimeField()
    reason = serializers.CharField(required=False, allow_blank=True, default="")
