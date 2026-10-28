from django.db import models


class Waitlist(models.Model):
    class Status(models.TextChoices):
        WAITING = "waiting", "Waiting"
        OFFERED = "offered", "Offered"
        BOOKED = "booked", "Booked"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="waitlist_entries")
    clinic = models.ForeignKey("clinics.Clinic", on_delete=models.CASCADE, related_name="waitlist_entries")
    provider = models.ForeignKey(
        "providers.Provider", on_delete=models.CASCADE, null=True, blank=True, related_name="waitlist_entries"
    )
    desired_date_range_start = models.DateField()
    desired_date_range_end = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WAITING)
    priority = models.PositiveSmallIntegerField(
        default=0, help_text="Higher number = higher priority. Ties broken by created_at (FIFO)."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-priority", "created_at"]
        indexes = [models.Index(fields=["clinic", "status"])]

    def __str__(self):
        return f"Waitlist #{self.id} {self.patient} @ {self.clinic} ({self.status})"


class WaitlistOffer(models.Model):
    class Response(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        EXPIRED = "expired", "Expired"

    waitlist_entry = models.ForeignKey(Waitlist, on_delete=models.CASCADE, related_name="offers")
    provider = models.ForeignKey("providers.Provider", on_delete=models.CASCADE, related_name="waitlist_offers")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    offered_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    response = models.CharField(max_length=10, choices=Response.choices, default=Response.PENDING)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-offered_at"]

    def __str__(self):
        return f"Offer #{self.id} for waitlist #{self.waitlist_entry_id} ({self.response})"
