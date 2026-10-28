from django.conf import settings
from django.db import models


class Provider(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="provider_profile"
    )
    home_clinic = models.ForeignKey(
        "clinics.Clinic", on_delete=models.PROTECT, related_name="home_providers"
    )
    specialty = models.CharField(max_length=255, blank=True, default="")
    license_number = models.CharField(max_length=100, blank=True, default="")
    is_active = models.BooleanField(default=True)

    # Convenience alias used by common.permissions.get_staff_clinic_ids.
    @property
    def clinic_id(self):
        return self.home_clinic_id

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.email}"


class ProviderClinicAssignment(models.Model):
    """Through-table supporting a provider working at multiple clinics,
    beyond their single `home_clinic`."""

    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="clinic_assignments")
    clinic = models.ForeignKey("clinics.Clinic", on_delete=models.CASCADE, related_name="provider_assignments")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("provider", "clinic")

    def __str__(self):
        return f"{self.provider} @ {self.clinic}"


class ProviderAvailability(models.Model):
    class Recurrence(models.TextChoices):
        WEEKLY = "weekly", "Weekly"
        ONE_OFF = "one_off", "One-off"

    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="availability_blocks")
    clinic = models.ForeignKey("clinics.Clinic", on_delete=models.CASCADE, related_name="availability_blocks")
    recurrence_rule = models.CharField(max_length=10, choices=Recurrence.choices, default=Recurrence.WEEKLY)

    # Exactly one of these is set, enforced in clean()/service layer:
    # - WEEKLY rules use day_of_week (0=Monday .. 6=Sunday, matching date.weekday()).
    # - ONE_OFF rules (including blackout overrides) use specific_date.
    day_of_week = models.PositiveSmallIntegerField(null=True, blank=True)
    specific_date = models.DateField(null=True, blank=True)

    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration_minutes = models.PositiveIntegerField(default=30)

    # A blocked entry represents time OFF (vacation, blackout) that
    # overrides/removes availability for that window rather than adding it.
    is_blocked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["provider_id", "day_of_week", "specific_date", "start_time"]
        constraints = [
            # Equal start/end is allowed deliberately: it's the convention
            # used for a one-off "whole day blocked" override (see
            # providers/services/slot_calculator.py), rather than a normal
            # time-of-day availability window.
            models.CheckConstraint(
                check=models.Q(start_time__lte=models.F("end_time")),
                name="availability_start_before_end",
            ),
        ]

    def __str__(self):
        when = f"day={self.day_of_week}" if self.recurrence_rule == self.Recurrence.WEEKLY else f"date={self.specific_date}"
        return f"{self.provider} {when} {self.start_time}-{self.end_time}"
