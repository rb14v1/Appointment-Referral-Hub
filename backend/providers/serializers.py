from rest_framework import serializers

from accounts.serializers import UserSerializer
from providers.models import Provider, ProviderAvailability, ProviderClinicAssignment


class ProviderClinicAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderClinicAssignment
        fields = ["id", "provider", "clinic", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProviderSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source="user", read_only=True)
    clinic_ids = serializers.SerializerMethodField()

    class Meta:
        model = Provider
        fields = [
            "id", "user", "user_detail", "home_clinic", "specialty",
            "license_number", "is_active", "clinic_ids",
        ]

    def get_clinic_ids(self, obj):
        ids = set(obj.clinic_assignments.filter(is_active=True).values_list("clinic_id", flat=True))
        ids.add(obj.home_clinic_id)
        return sorted(ids)


class ProviderAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderAvailability
        fields = [
            "id", "provider", "clinic", "recurrence_rule", "day_of_week",
            "specific_date", "start_time", "end_time", "slot_duration_minutes",
            "is_blocked", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        recurrence = attrs.get("recurrence_rule", getattr(self.instance, "recurrence_rule", None))
        day_of_week = attrs.get("day_of_week", getattr(self.instance, "day_of_week", None))
        specific_date = attrs.get("specific_date", getattr(self.instance, "specific_date", None))
        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))

        if recurrence == ProviderAvailability.Recurrence.WEEKLY:
            if day_of_week is None:
                raise serializers.ValidationError("day_of_week is required for weekly recurrence.")
            if specific_date is not None:
                raise serializers.ValidationError("specific_date must be empty for weekly recurrence.")
        elif recurrence == ProviderAvailability.Recurrence.ONE_OFF:
            if specific_date is None:
                raise serializers.ValidationError("specific_date is required for one-off recurrence.")
            if day_of_week is not None:
                raise serializers.ValidationError("day_of_week must be empty for one-off recurrence.")

        if start_time is not None and end_time is not None and start_time > end_time:
            raise serializers.ValidationError(
                "start_time must be before (or, for a whole-day block, equal to) end_time."
            )

        return attrs


class SlotQuerySerializer(serializers.Serializer):
    clinic = serializers.IntegerField(required=False)
    date_from = serializers.DateField()
    date_to = serializers.DateField()

    def validate(self, attrs):
        if attrs["date_from"] > attrs["date_to"]:
            raise serializers.ValidationError("date_from must be on or before date_to.")
        return attrs


class SlotSerializer(serializers.Serializer):
    provider = serializers.IntegerField()
    clinic = serializers.IntegerField()
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
