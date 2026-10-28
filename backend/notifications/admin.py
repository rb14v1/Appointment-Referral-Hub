from django.contrib import admin

from notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "type", "channel", "status", "scheduled_for", "sent_at"]
    list_filter = ["status", "channel", "type"]
