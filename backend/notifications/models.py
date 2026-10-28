from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"
        IN_APP = "in_app", "In-app"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(
        max_length=50,
        help_text="e.g. 'appointment_reminder_24h', 'appointment_reminder_1h', 'waitlist_offer', 'referral_status'",
    )
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.EMAIL)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    scheduled_for = models.DateTimeField()
    # Guard against double-sends (e.g. a Celery beat task re-running after a
    # worker restart): `send_due_reminders` only ever acts on rows where
    # sent_at IS NULL, and sets it atomically with status=SENT.
    sent_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-scheduled_for"]
        indexes = [models.Index(fields=["status", "scheduled_for"])]

    def __str__(self):
        return f"Notification #{self.id} to {self.user} ({self.type}, {self.status})"
