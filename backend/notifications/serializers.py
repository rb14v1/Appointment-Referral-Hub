from rest_framework import serializers

from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "user", "type", "channel", "payload", "status", "scheduled_for", "sent_at", "created_at"]
        read_only_fields = fields
