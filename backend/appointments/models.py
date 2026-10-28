from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeOperators
from django.db import models
from django.db.models import Func, Q


class Appointment(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        CONFIRMED = "confirmed", "Confirmed"
        CHECKED_IN = "checked_in", "Checked In"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No Show"

    ACTIVE_STATUSES = [Status.REQUESTED, Status.CONFIRMED, Status.CHECKED_IN]

    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="appointments")
    provider = models.ForeignKey("providers.Provider", on_delete=models.CASCADE, related_name="appointments")
    clinic = models.ForeignKey("clinics.Clinic", on_delete=models.CASCADE, related_name="appointments")

    start_time = models.DateTimeField(help_text="Stored in UTC; convert to clinic.timezone for display.")
    end_time = models.DateTimeField(help_text="Stored in UTC; convert to clinic.timezone for display.")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED)
    reason = models.TextField(blank=True, default="")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_appointments"
    )
    referral = models.ForeignKey(
        "referrals.Referral", on_delete=models.SET_NULL, null=True, blank=True, related_name="appointments"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_time"]
        constraints = [
            models.CheckConstraint(
                check=Q(start_time__lt=models.F("end_time")),
                name="appointment_start_before_end",
            ),
            # PostgreSQL-only: prevents any two ACTIVE (requested/confirmed/
            # checked_in) appointments for the same provider from having
            # overlapping [start_time, end_time) ranges, enforced atomically
            # by the database itself (closes the race window that a plain
            # application-level check + select_for_update can still miss
            # under certain isolation levels). Requires the btree_gist
            # extension (enabled via a migration operation - see
            # appointments/migrations/0002_*). On non-Postgres backends
            # (e.g. SQLite in local/dev/test runs without a Postgres
            # server) the migration that adds this constraint is a guarded
            # no-op — see common/migration_operations.py — so the
            # application still runs, but double-booking protection then
            # relies solely on the select_for_update()-guarded
            # transaction in appointments/services/booking.py.
            ExclusionConstraint(
                name="exclude_overlapping_active_appointments_per_provider",
                expressions=[
                    ("provider", RangeOperators.EQUAL),
                    (Func("start_time", "end_time", function="tstzrange"), RangeOperators.OVERLAPS),
                ],
                condition=Q(status__in=["requested", "confirmed", "checked_in"]),
            ),
        ]
        indexes = [
            models.Index(fields=["provider", "start_time"]),
            models.Index(fields=["clinic", "start_time"]),
            models.Index(fields=["patient", "start_time"]),
        ]

    def __str__(self):
        return f"{self.patient} with {self.provider} @ {self.start_time.isoformat()}"
