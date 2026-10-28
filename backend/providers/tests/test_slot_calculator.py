from datetime import datetime, time, timedelta

from django.test import TestCase
from django.utils import timezone

from appointments.services.booking import book_appointment
from common.test_utils import make_clinic, make_patient, make_provider
from providers.models import ProviderAvailability
from providers.services.slot_calculator import get_available_slots


class SlotCalculatorTests(TestCase):
    def setUp(self):
        self.clinic = make_clinic("Main Clinic")
        # Weekday availability Mon(0)-Fri(4), 09:00-10:00, 30-min slots -> 2 slots/day.
        self.provider = make_provider("doc@example.com", self.clinic, slot_duration=30, availability_days=[0])
        ProviderAvailability.objects.filter(provider=self.provider).update(start_time=time(9, 0), end_time=time(10, 0))

        # Find the next Monday.
        today = timezone.localdate()
        days_ahead = (7 - today.weekday()) % 7 or 7
        self.next_monday = today + timedelta(days=days_ahead)

    def test_generates_slots_from_weekly_rule(self):
        slots = get_available_slots(self.provider, self.next_monday, self.next_monday)
        self.assertEqual(len(slots), 2)
        self.assertEqual(slots[0].start.time().replace(tzinfo=None), time(9, 0))
        self.assertEqual(slots[1].start.time().replace(tzinfo=None), time(9, 30))

    def test_excludes_non_matching_weekday(self):
        tuesday = self.next_monday + timedelta(days=1)
        slots = get_available_slots(self.provider, tuesday, tuesday)
        self.assertEqual(slots, [])

    def test_removes_slots_already_booked(self):
        patient = make_patient("pat@example.com", primary_clinic=self.clinic)
        start_dt = timezone.make_aware(datetime.combine(self.next_monday, time(9, 0)))
        book_appointment(patient=patient, provider=self.provider, clinic=self.clinic, start_time=start_dt, created_by=patient.user)

        slots = get_available_slots(self.provider, self.next_monday, self.next_monday)
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0].start, start_dt + timedelta(minutes=30))

    def test_one_off_blocked_date_removes_full_day(self):
        ProviderAvailability.objects.create(
            provider=self.provider, clinic=self.clinic,
            recurrence_rule=ProviderAvailability.Recurrence.ONE_OFF,
            specific_date=self.next_monday,
            start_time=time(0, 0), end_time=time(0, 0),
            is_blocked=True,
        )
        slots = get_available_slots(self.provider, self.next_monday, self.next_monday)
        self.assertEqual(slots, [])

    def test_one_off_extra_availability_adds_slots_on_otherwise_closed_day(self):
        saturday = self.next_monday + timedelta(days=5)
        ProviderAvailability.objects.create(
            provider=self.provider, clinic=self.clinic,
            recurrence_rule=ProviderAvailability.Recurrence.ONE_OFF,
            specific_date=saturday,
            start_time=time(9, 0), end_time=time(10, 0),
            slot_duration_minutes=30,
        )
        slots = get_available_slots(self.provider, saturday, saturday)
        self.assertEqual(len(slots), 2)
