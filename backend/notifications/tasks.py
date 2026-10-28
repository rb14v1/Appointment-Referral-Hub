"""
Notification dispatch. `schedule_appointment_reminders` creates the T-24h
and T-1h Notification rows when an appointment is confirmed; `send_due_reminders`
is the Celery-beat-driven sweep that actually "sends" (here: logs/stubs the
send - wiring a real email/SMS provider is out of scope) anything due.

Idempotency: `send_due_reminders` only selects rows with `sent_at IS NULL`
and `status='pending'`, and sets both atomically per-row, so re-running the
sweep (e.g. after a worker restart mid-batch) never double-sends.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone as dj_timezone

from notifications.models import Notification

logger = logging.getLogger(__name__)


def schedule_appointment_reminders(appointment):
    """Create (idempotently) the two reminder Notification rows for a newly
    confirmed appointment. Safe to call more than once - uses get_or_create
    keyed on (user, type, scheduled_for) via the payload's appointment id."""
    reminders = [
        ("appointment_reminder_24h", appointment.start_time - timedelta(hours=24)),
        ("appointment_reminder_1h", appointment.start_time - timedelta(hours=1)),
    ]
    created = []
    for reminder_type, scheduled_for in reminders:
        if scheduled_for < dj_timezone.now():
            continue  # don't schedule reminders in the past
        notification, _ = Notification.objects.get_or_create(
            user=appointment.patient.user,
            type=reminder_type,
            payload__appointment_id=appointment.id,
            defaults={
                "channel": Notification.Channel.EMAIL,
                "payload": {"appointment_id": appointment.id},
                "scheduled_for": scheduled_for,
                "status": Notification.Status.PENDING,
            },
        )
        created.append(notification)
    return created


def _dispatch(notification):
    """Stand-in for a real email/SMS integration."""
    logger.info("Sending notification %s to %s (%s)", notification.id, notification.user_id, notification.type)
    return True


def send_due_reminders_now():
    due = Notification.objects.filter(
        status=Notification.Status.PENDING,
        sent_at__isnull=True,
        scheduled_for__lte=dj_timezone.now(),
    )
    sent_count = 0
    for notification in due:
        with transaction.atomic():
            locked = Notification.objects.select_for_update().get(id=notification.id)
            if locked.sent_at is not None:
                continue  # already sent by a concurrent worker
            if _dispatch(locked):
                locked.status = Notification.Status.SENT
                locked.sent_at = dj_timezone.now()
                locked.save(update_fields=["status", "sent_at"])
                sent_count += 1
    return sent_count


@shared_task(name="notifications.tasks.send_due_reminders")
def send_due_reminders():
    return send_due_reminders_now()
