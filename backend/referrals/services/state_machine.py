"""
Referral state machine.

Explicit allowed-transition map — anything not listed here is illegal and
`transition()` raises IllegalTransitionError (-> HTTP 409 at the API layer).

    pending   -> accepted, rejected, cancelled
    accepted  -> scheduled, cancelled
    scheduled -> completed, cancelled
    rejected, completed, cancelled -> (terminal; no further transitions)
"""
from django.db import transaction
from django.utils import timezone

from common.exceptions import ConflictError
from referrals.models import Referral

TERMINAL_STATUSES = {Referral.Status.REJECTED, Referral.Status.COMPLETED, Referral.Status.CANCELLED}

ALLOWED_TRANSITIONS = {
    Referral.Status.PENDING: {Referral.Status.ACCEPTED, Referral.Status.REJECTED, Referral.Status.CANCELLED},
    Referral.Status.ACCEPTED: {Referral.Status.SCHEDULED, Referral.Status.CANCELLED},
    Referral.Status.SCHEDULED: {Referral.Status.COMPLETED, Referral.Status.CANCELLED},
    Referral.Status.REJECTED: set(),
    Referral.Status.COMPLETED: set(),
    Referral.Status.CANCELLED: set(),
}


class IllegalTransitionError(ConflictError):
    pass


@transaction.atomic
def transition(referral: Referral, new_status, *, actor=None, notes=None):
    """Move `referral` to `new_status` if the transition is legal; raise
    IllegalTransitionError otherwise. `actor` is accepted for future
    audit-logging hooks (not currently persisted on Referral itself)."""
    current = referral.status
    allowed = ALLOWED_TRANSITIONS.get(current, set())

    if new_status not in allowed:
        raise IllegalTransitionError(
            f"Cannot transition referral from '{current}' to '{new_status}'.",
            detail={
                "current_status": current,
                "requested_status": new_status,
                "allowed_next_statuses": sorted(allowed) if allowed else [],
            },
        )

    referral.status = new_status
    if notes:
        referral.notes = f"{referral.notes}\n{notes}".strip()
    if new_status in TERMINAL_STATUSES or new_status == Referral.Status.COMPLETED:
        referral.resolved_at = timezone.now()

    referral.save(update_fields=["status", "notes", "resolved_at"])
    return referral


def accept(referral, *, actor, receiving_provider=None, notes=None):
    if receiving_provider is not None:
        referral.receiving_provider = receiving_provider
        referral.save(update_fields=["receiving_provider"])
    return transition(referral, Referral.Status.ACCEPTED, actor=actor, notes=notes)


def reject(referral, *, actor, notes=None):
    return transition(referral, Referral.Status.REJECTED, actor=actor, notes=notes)


def mark_scheduled(referral, *, actor, notes=None):
    """Called once an Appointment has been booked against this referral."""
    return transition(referral, Referral.Status.SCHEDULED, actor=actor, notes=notes)


def cancel(referral, *, actor, notes=None):
    return transition(referral, Referral.Status.CANCELLED, actor=actor, notes=notes)
