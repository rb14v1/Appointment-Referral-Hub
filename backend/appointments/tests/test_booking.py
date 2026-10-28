from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from appointments.models import Appointment
from appointments.services.booking import book_appointment, cancel_appointment
from common.exceptions import ConflictError
from common.test_utils import make_clinic, make_patient, make_provider


class BookingServiceTests(TestCase):
    def setUp(self):
        self.clinic = make_clinic("Main Clinic")
        self.provider = make_provider("doc@example.com", self.clinic)
        self.patient = make_patient("pat@example.com", primary_clinic=self.clinic)
        self.staff = self.provider.user

        # Next Monday at 09:00 UTC, guaranteed in the future.
        now = timezone.now()
        days_ahead = (7 - now.weekday()) % 7 or 7
        self.start = (now + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0, microsecond=0)

    def test_books_confirmed_appointment(self):
        appt = book_appointment(
            patient=self.patient,
            provider=self.provider,
            clinic=self.clinic,
            start_time=self.start,
            created_by=self.staff,
        )
        self.assertEqual(appt.status, Appointment.Status.CONFIRMED)
        self.assertEqual(appt.end_time, self.start + timedelta(minutes=30))

    def test_rejects_double_booking_same_provider(self):
        book_appointment(
            patient=self.patient, provider=self.provider, clinic=self.clinic,
            start_time=self.start, created_by=self.staff,
        )
        other_patient = make_patient("pat2@example.com", primary_clinic=self.clinic)
        with self.assertRaises(ConflictError):
            book_appointment(
                patient=other_patient, provider=self.provider, clinic=self.clinic,
                start_time=self.start, created_by=self.staff,
            )

    def test_allows_booking_after_cancellation_frees_slot(self):
        appt = book_appointment(
            patient=self.patient, provider=self.provider, clinic=self.clinic,
            start_time=self.start, created_by=self.staff,
        )
        cancel_appointment(appt, actor=self.staff)

        other_patient = make_patient("pat3@example.com", primary_clinic=self.clinic)
        appt2 = book_appointment(
            patient=other_patient, provider=self.provider, clinic=self.clinic,
            start_time=self.start, created_by=self.staff,
        )
        self.assertEqual(appt2.status, Appointment.Status.CONFIRMED)

    def test_rejects_booking_in_the_past(self):
        past = timezone.now() - timedelta(days=1)
        with self.assertRaises(ConflictError):
            book_appointment(
                patient=self.patient, provider=self.provider, clinic=self.clinic,
                start_time=past, created_by=self.staff,
            )

    def test_requires_front_desk_approval_flag(self):
        self.clinic.requires_front_desk_approval = True
        self.clinic.save()
        appt = book_appointment(
            patient=self.patient, provider=self.provider, clinic=self.clinic,
            start_time=self.start, created_by=self.staff,
        )
        self.assertEqual(appt.status, Appointment.Status.REQUESTED)
