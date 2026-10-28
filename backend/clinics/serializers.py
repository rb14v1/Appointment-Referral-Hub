from rest_framework import serializers

from clinics.models import Clinic


class ClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = [
            "id", "name", "address", "timezone", "phone", "is_active",
            "requires_front_desk_approval",
        ]
