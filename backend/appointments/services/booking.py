"""
Booking service: the single place that creates an Appointment.

Double-booking defence in depth:
1. Application-level: inside `transaction.atomic()`, `select_for_update()`
   locks the provider's existing active-status appointment rows that could
   overlap the requested window, so two concurrent requests for the same
   provider serialize instead of racing.
2. Database-level (Postgres only): the ExclusionConstraint on Appointment
   (see appointments/models.py) rejects any overlapping insert even if the
   application-level check were somehow bypassed (e.g. a second process
   connected directly to the DB). We catch IntegrityError from that
   constraint and translate it into the same clean ConflictError the
   application-level check raises, so callers (the API view) only ever have
   to handle one exception type.

On non-Postgres backends (no exclusion constraint available - see
common/migration_operations.py) the select_for_update()-guarded check below
is the sole guard; this is documented, not silent.
"""
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone as dj_timezone

from appointments.models import Appointment
from common.exceptions import ConflictError


def _overlap_qs(provider, start_time, end_time, exclude_id=None):
    qs = Appointment.objects.select_for_update().filter(
        provider=provider,
        status__in=Appointment.ACTIVE_STATUSES,
        start_time__lt=end_time,
        end_time__gt=start_time,
    )
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)
    return qs


@transaction.atomic
def book_appointment(*, patient, provider, clinic, start_time, reason="", created_by, referral=None, slot_duration_minutes=None):
    """Create a confirmed (or requested, if the clinic requires front-desk
    approval) Appointment for `patient` with `provider` at `clinic` starting
    at `start_time` (an aware UTC datetime).

    Raises ConflictError if the slot is no longer available.
    """
    if dj_timezone.is_naive(start_time):
        raise ValueError("start_time must be timezone-aware (UTC).")

    duration = slot_duration_minutes
    if duration is None:
        rule = provider.availability_blocks.filter(clinic=clinic).order_by("-id").first()
        duration = rule.slot_duration_minutes if rule else 30
    end_time = start_time + timedelta(minutes=duration)

    if start_time < dj_timezone.now():
        raise ConflictError("Cannot book an appointment in the past.")

    # Lock the window first (keeps a serialized ordering for concurrent
    # requests against the same provider even before we try the insert).
    if _overlap_qs(provider, start_time, end_time).exists():
        raise ConflictError("This provider already has an appointment in that window.")

    initial_status = Appointment.Status.CONFIRMED
    if getattr(clinic, "requires_front_desk_approval", False):
        initial_status = Appointment.Status.REQUESTED

    try:
        with transaction.atomic():
            appointment = Appointment.objects.create(
                patient=patient,
                provider=provider,
                clinic=clinic,
                start_time=start_time,
                end_time=end_time,
                status=initial_status,
                reason=reason,
                created_by=created_by,
                referral=referral,
            )
    except IntegrityError as exc:
        raise ConflictError(
            "This provider already has an appointment in that window.",
            detail=str(exc),
        ) from exc

    if appointment.status == Appointment.Status.CONFIRMED:
        from notifications.tasks import schedule_appointment_reminders

        schedule_appointment_reminders(appointment)

    return appointment


@transaction.atomic
def cancel_appointment(appointment, *, actor, reason=""):
    """Cancel an appointment. If it originated from a referral, the referral
    is left as-is (explicit revert-vs-cancel rule: cancelling the
    appointment does NOT automatically revert the referral to 'accepted' -
    a front-desk/clinician must explicitly re-schedule or cancel the
    referral too) - this avoids silently resurrecting a referral the
    receiving clinic may have already closed out.
    """
    if appointment.status in (Appointment.Status.CANCELLED, Appointment.Status.COMPLETED):
        raise ConflictError(f"Cannot cancel an appointment that is already {appointment.status}.")

    appointment.status = Appointment.Status.CANCELLED
    appointment.save(update_fields=["status", "updated_at"])

    # Fire waitlist matching synchronously-or-async: a slot just freed up.
    from waitlist.tasks import match_waitlist_for_slot

    match_waitlist_for_slot.delay(
        clinic_id=appointment.clinic_id,
        provider_id=appointment.provider_id,
        start_time=appointment.start_time.isoformat(),
        end_time=appointment.end_time.isoformat(),
    )
    return appointment


def check_in_appointment(appointment):
    if appointment.status != Appointment.Status.CONFIRMED:
        raise ConflictError(f"Cannot check in an appointment with status '{appointment.status}'.")
    appointment.status = Appointment.Status.CHECKED_IN
    appointment.save(update_fields=["status", "updated_at"])
    return appointment


def complete_appointment(appointment):
    if appointment.status != Appointment.Status.CHECKED_IN:
        raise ConflictError(f"Cannot complete an appointment with status '{appointment.status}'.")
    appointment.status = Appointment.Status.COMPLETED
    appointment.save(update_fields=["status", "updated_at"])

    if appointment.referral_id:
        from referrals.models import Referral
        from referrals.services.state_machine import transition

        referral = appointment.referral
        if referral.status == Referral.Status.SCHEDULED:
            transition(referral, Referral.Status.COMPLETED, actor=appointment.created_by)

    return appointment


def mark_no_show(appointment):
    if appointment.status not in (Appointment.Status.CONFIRMED, Appointment.Status.CHECKED_IN):
        raise ConflictError(f"Cannot mark no-show for an appointment with status '{appointment.status}'.")
    appointment.status = Appointment.Status.NO_SHOW
    appointment.save(update_fields=["status", "updated_at"])
    return appointment
