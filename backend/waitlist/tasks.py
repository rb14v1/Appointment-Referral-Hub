"""
Waitlist matching, implemented as plain functions (synchronously callable,
e.g. from tests, with no broker required) and thin Celery task wrappers
around them (for the real async/scheduled paths: a slot freeing up on
cancellation, and periodic offer-expiry sweeps).

Matching rule: clinic must match; provider, if the waitlist entry specifies
one, must match; the freed slot's date must fall within
[desired_date_range_start, desired_date_range_end]. Among matches, highest
`priority` wins, ties broken FIFO by `created_at`.
"""
from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone as dj_timezone
from django.utils.dateparse import parse_datetime

from waitlist.models import Waitlist, WaitlistOffer


def _offer_expiry():
    hours = getattr(settings, "WAITLIST_OFFER_EXPIRY_HOURS", 2)
    return dj_timezone.now() + timedelta(hours=hours)


@transaction.atomic
def find_and_offer_match(*, clinic_id, provider_id, start_time: datetime, end_time: datetime):
    """Find the best-matching WAITING waitlist entry for a slot that just
    became free and create a WaitlistOffer for it. Returns the created
    WaitlistOffer, or None if no entry matches.

    Locked with select_for_update to avoid two concurrent cancellations
    both offering the same entry the same (or different) slot twice.
    """
    slot_date = dj_timezone.localtime(start_time).date()

    # Exclude entries that already turned down (declined/expired) an offer
    # for this exact slot - otherwise a decline would immediately re-offer
    # the same slot to the same entry instead of advancing to the next
    # candidate.
    already_passed_entry_ids = WaitlistOffer.objects.filter(
        provider_id=provider_id,
        start_time=start_time,
        end_time=end_time,
        response__in=[WaitlistOffer.Response.DECLINED, WaitlistOffer.Response.EXPIRED],
    ).values_list("waitlist_entry_id", flat=True)

    candidates = (
        Waitlist.objects.select_for_update()
        .filter(
            clinic_id=clinic_id,
            status=Waitlist.Status.WAITING,
            desired_date_range_start__lte=slot_date,
            desired_date_range_end__gte=slot_date,
        )
        .exclude(id__in=list(already_passed_entry_ids))
        .filter(models_q_provider(provider_id))
        .order_by("-priority", "created_at")
    )

    entry = candidates.first()
    if entry is None:
        return None

    offer = WaitlistOffer.objects.create(
        waitlist_entry=entry,
        provider_id=provider_id,
        start_time=start_time,
        end_time=end_time,
        expires_at=_offer_expiry(),
        response=WaitlistOffer.Response.PENDING,
    )
    entry.status = Waitlist.Status.OFFERED
    entry.save(update_fields=["status"])
    return offer


def models_q_provider(provider_id):
    from django.db.models import Q
    return Q(provider_id=provider_id) | Q(provider_id__isnull=True)


@transaction.atomic
def respond_to_offer(offer: WaitlistOffer, accept: bool):
    """Patient accepts or declines an offer. On decline, the slot is
    re-offered to the next matching candidate (auto-advance); on accept,
    the caller is still responsible for actually booking the Appointment
    (see waitlist/views.py), after which the entry is marked booked."""
    if offer.response != WaitlistOffer.Response.PENDING:
        from common.exceptions import ConflictError

        raise ConflictError(f"This offer has already been responded to ({offer.response}).")

    offer.response = WaitlistOffer.Response.ACCEPTED if accept else WaitlistOffer.Response.DECLINED
    offer.responded_at = dj_timezone.now()
    offer.save(update_fields=["response", "responded_at"])

    entry = offer.waitlist_entry
    if accept:
        entry.status = Waitlist.Status.BOOKED
        entry.save(update_fields=["status"])
    else:
        entry.status = Waitlist.Status.WAITING
        entry.save(update_fields=["status"])
        find_and_offer_match(
            clinic_id=entry.clinic_id,
            provider_id=offer.provider_id,
            start_time=offer.start_time,
            end_time=offer.end_time,
        )
    return offer


@transaction.atomic
def expire_offer(offer: WaitlistOffer):
    if offer.response != WaitlistOffer.Response.PENDING:
        return offer
    offer.response = WaitlistOffer.Response.EXPIRED
    offer.responded_at = dj_timezone.now()
    offer.save(update_fields=["response", "responded_at"])

    entry = offer.waitlist_entry
    entry.status = Waitlist.Status.WAITING
    entry.save(update_fields=["status"])

    find_and_offer_match(
        clinic_id=entry.clinic_id,
        provider_id=offer.provider_id,
        start_time=offer.start_time,
        end_time=offer.end_time,
    )
    return offer


def expire_due_offers_now():
    """Plain, synchronous sweep used by both the Celery beat task below and
    tests: expires every still-pending offer past its `expires_at`."""
    due = WaitlistOffer.objects.filter(
        response=WaitlistOffer.Response.PENDING, expires_at__lt=dj_timezone.now()
    )
    count = 0
    for offer in due:
        expire_offer(offer)
        count += 1
    return count


# ---------------------------------------------------------------------------
# Celery task wrappers
# ---------------------------------------------------------------------------
@shared_task(name="waitlist.tasks.match_waitlist_for_slot")
def match_waitlist_for_slot(*, clinic_id, provider_id, start_time, end_time):
    start_dt = parse_datetime(start_time) if isinstance(start_time, str) else start_time
    end_dt = parse_datetime(end_time) if isinstance(end_time, str) else end_time
    offer = find_and_offer_match(clinic_id=clinic_id, provider_id=provider_id, start_time=start_dt, end_time=end_dt)
    return offer.id if offer else None


@shared_task(name="waitlist.tasks.expire_stale_offers")
def expire_stale_offers():
    return expire_due_offers_now()
