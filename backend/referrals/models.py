from django.conf import settings
from django.db import models


class Referral(models.Model):
    class Urgency(models.TextChoices):
        ROUTINE = "routine", "Routine"
        URGENT = "urgent", "Urgent"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="referrals")
    referring_clinic = models.ForeignKey("clinics.Clinic", on_delete=models.CASCADE, related_name="referrals_sent")
    referring_provider = models.ForeignKey(
        "providers.Provider", on_delete=models.SET_NULL, null=True, related_name="referrals_made"
    )
    receiving_clinic = models.ForeignKey("clinics.Clinic", on_delete=models.CASCADE, related_name="referrals_received")
    receiving_provider = models.ForeignKey(
        "providers.Provider", on_delete=models.SET_NULL, null=True, blank=True, related_name="referrals_assigned"
    )
    reason = models.TextField()
    urgency = models.CharField(max_length=10, choices=Urgency.choices, default=Urgency.ROUTINE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True, default="")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_referrals"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["receiving_clinic", "status"]),
            models.Index(fields=["patient", "status"]),
        ]

    def __str__(self):
        return f"Referral #{self.id} {self.patient} -> {self.receiving_clinic} ({self.status})"
