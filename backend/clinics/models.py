from django.db import models


class Clinic(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500, blank=True, default="")
    timezone = models.CharField(
        max_length=64,
        default="UTC",
        help_text="IANA timezone name, e.g. 'America/New_York'. All appointment "
        "times are stored in UTC and converted to this timezone for display.",
    )
    phone = models.CharField(max_length=32, blank=True, default="")
    is_active = models.BooleanField(default=True)
    # When True, patient-initiated bookings are created with status
    # "requested" and must be confirmed by front desk, instead of auto-confirming.
    requires_front_desk_approval = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
