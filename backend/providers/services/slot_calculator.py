"""
Slot calculation: turns a provider's ProviderAvailability rules into a list
of concrete, bookable (start, end) slots for a date range, after removing
anything already taken by a non-cancelled Appointment.

Algorithm:
1. Pull all availability rows for the provider (optionally scoped to one
   clinic) that could apply within [range_start, range_end].
2. For each calendar date in the range:
   a. Find WEEKLY rules matching that date's weekday that are NOT blocked.
   b. Find ONE_OFF rules with specific_date == that date that are NOT
      blocked - these ADD availability for that date (e.g. an extra Saturday
      clinic).
   c. Expand each applicable rule into fixed-length slots of
      `slot_duration_minutes`.
   d. Remove any slot that falls inside a ONE_OFF rule with specific_date ==
      that date AND is_blocked=True (a full or partial-day block/vacation
      override for that specific date) - this lets a one-off blocked entry
      override part or all of a recurring weekly rule for a single day.
3. Subtract any slot that overlaps an existing Appointment for that provider
   with status NOT IN (cancelled, no_show).
4. Return sorted, deduplicated (start, end) tuples, each tagged with the
   clinic they belong to.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from django.utils import timezone as dj_timezone


@dataclass(frozen=True)
class Slot:
    start: datetime
    end: datetime
    clinic_id: int
    provider_id: int

    def overlaps(self, other_start: datetime, other_end: datetime) -> bool:
        return self.start < other_end and other_start < self.end


def _daterange(start: date, end: date):
    for n in range((end - start).days + 1):
        yield start + timedelta(days=n)


def _expand_rule_to_slots(rule, the_date: date) -> list[Slot]:
    """Expand one ProviderAvailability row into same-day fixed-duration slots."""
    tz = dj_timezone.get_default_timezone()
    naive_start = datetime.combine(the_date, rule.start_time)
    naive_end = datetime.combine(the_date, rule.end_time)
    start_dt = dj_timezone.make_aware(naive_start, tz) if dj_timezone.is_naive(naive_start) else naive_start
    end_dt = dj_timezone.make_aware(naive_end, tz) if dj_timezone.is_naive(naive_end) else naive_end

    step = timedelta(minutes=rule.slot_duration_minutes)
    slots = []
    cursor = start_dt
    while cursor + step <= end_dt:
        slots.append(Slot(start=cursor, end=cursor + step, clinic_id=rule.clinic_id, provider_id=rule.provider_id))
        cursor += step
    return slots


def get_available_slots(provider, range_start: date, range_end: date, clinic=None):
    """Return a sorted list of bookable Slot objects for `provider` between
    range_start and range_end (inclusive), optionally restricted to one clinic.
    """
    from appointments.models import Appointment  # local import avoids app-loading cycles
    from providers.models import ProviderAvailability

    rules_qs = ProviderAvailability.objects.filter(provider=provider)
    if clinic is not None:
        rules_qs = rules_qs.filter(clinic=clinic)

    weekly_rules = [r for r in rules_qs if r.recurrence_rule == ProviderAvailability.Recurrence.WEEKLY and not r.is_blocked]
    one_off_open_rules = [r for r in rules_qs if r.recurrence_rule == ProviderAvailability.Recurrence.ONE_OFF and not r.is_blocked]
    one_off_blocked_rules = [r for r in rules_qs if r.recurrence_rule == ProviderAvailability.Recurrence.ONE_OFF and r.is_blocked]

    candidate_slots: list[Slot] = []

    for the_date in _daterange(range_start, range_end):
        day_blocks_full_day = any(
            r.specific_date == the_date for r in one_off_blocked_rules
            if r.start_time == r.end_time  # a (start==end) blocked row is treated as "whole day off"
        )
        if day_blocks_full_day:
            continue

        day_slots: list[Slot] = []
        for rule in weekly_rules:
            if rule.day_of_week == the_date.weekday():
                day_slots.extend(_expand_rule_to_slots(rule, the_date))

        for rule in one_off_open_rules:
            if rule.specific_date == the_date:
                day_slots.extend(_expand_rule_to_slots(rule, the_date))

        # Remove slots covered by a partial-day block for this specific date.
        blocking_windows = [
            (r.start_time, r.end_time) for r in one_off_blocked_rules
            if r.specific_date == the_date and r.start_time != r.end_time
        ]
        if blocking_windows:
            kept = []
            for slot in day_slots:
                slot_start_t = dj_timezone.localtime(slot.start).time()
                blocked = any(bs <= slot_start_t < be for bs, be in blocking_windows)
                if not blocked:
                    kept.append(slot)
            day_slots = kept

        candidate_slots.extend(day_slots)

    if not candidate_slots:
        return []

    range_start_dt = dj_timezone.make_aware(datetime.combine(range_start, datetime.min.time()))
    range_end_dt = dj_timezone.make_aware(datetime.combine(range_end + timedelta(days=1), datetime.min.time()))

    existing_appointments = Appointment.objects.filter(
        provider=provider,
        start_time__lt=range_end_dt,
        end_time__gt=range_start_dt,
    ).exclude(status__in=["cancelled", "no_show"])

    busy_windows = [(a.start_time, a.end_time) for a in existing_appointments]

    free_slots = [
        slot for slot in candidate_slots
        if not any(slot.overlaps(bstart, bend) for bstart, bend in busy_windows)
    ]

    free_slots.sort(key=lambda s: s.start)
    # Deduplicate (two overlapping availability rules could generate the
    # same slot twice).
    seen = set()
    deduped = []
    for slot in free_slots:
        key = (slot.start, slot.end, slot.clinic_id)
        if key not in seen:
            seen.add(key)
            deduped.append(slot)
    return deduped
