from rest_framework import serializers

from waitlist.models import Waitlist, WaitlistOffer


class WaitlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Waitlist
        fields = [
            "id", "patient", "clinic", "provider", "desired_date_range_start",
            "desired_date_range_end", "status", "priority", "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]


class WaitlistOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaitlistOffer
        fields = [
            "id", "waitlist_entry", "provider", "start_time", "end_time",
            "offered_at", "expires_at", "response", "responded_at",
        ]
        read_only_fields = fields


class WaitlistOfferResponseSerializer(serializers.Serializer):
    accept = serializers.BooleanField()
