from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from common.test_utils import make_clinic, make_patient, make_provider
from notifications.models import Notification
from notifications.tasks import schedule_appointment_reminders, send_due_reminders_now
from appointments.services.booking import book_appointment


class NotificationSchedulingTests(TestCase):
    def setUp(self):
        self.clinic = make_clinic("Main Clinic")
        self.provider = make_provider("doc@example.com", self.clinic)
        self.patient = make_patient("pat@example.com", primary_clinic=self.clinic)

    def test_booking_schedules_two_reminders(self):
        now = timezone.now()
        days_ahead = (7 - now.weekday()) % 7 or 7
        start = (now + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0, microsecond=0)
        appt = book_appointment(
            patient=self.patient, provider=self.provider, clinic=self.clinic,
            start_time=start, created_by=self.patient.user,
        )
        notifications = Notification.objects.filter(payload__appointment_id=appt.id)
        self.assertEqual(notifications.count(), 2)

    def test_scheduling_is_idempotent(self):
        now = timezone.now()
        days_ahead = (7 - now.weekday()) % 7 or 7
        start = (now + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0, microsecond=0)
        appt = book_appointment(
            patient=self.patient, provider=self.provider, clinic=self.clinic,
            start_time=start, created_by=self.patient.user,
        )
        schedule_appointment_reminders(appt)
        schedule_appointment_reminders(appt)
        notifications = Notification.objects.filter(payload__appointment_id=appt.id)
        self.assertEqual(notifications.count(), 2)

    def test_send_due_reminders_sets_sent_at_once(self):
        notification = Notification.objects.create(
            user=self.patient.user, type="appointment_reminder_1h",
            scheduled_for=timezone.now() - timedelta(minutes=1),
        )
        sent = send_due_reminders_now()
        self.assertEqual(sent, 1)
        notification.refresh_from_db()
        self.assertEqual(notification.status, Notification.Status.SENT)
        self.assertIsNotNone(notification.sent_at)

        # Re-running must not re-send (sent_at guard).
        sent_again = send_due_reminders_now()
        self.assertEqual(sent_again, 0)


class NotificationIsolationTests(APITestCase):
    def setUp(self):
        self.clinic = make_clinic("Clinic A")
        self.patient_a = make_patient("pat.a@example.com", primary_clinic=self.clinic)
        self.patient_b = make_patient("pat.b@example.com", primary_clinic=self.clinic)
        self.notif_a = Notification.objects.create(
            user=self.patient_a.user, type="test", scheduled_for=timezone.now()
        )
        self.notif_b = Notification.objects.create(
            user=self.patient_b.user, type="test", scheduled_for=timezone.now()
        )

    def test_user_only_sees_own_notifications(self):
        self.client.force_authenticate(self.patient_a.user)
        response = self.client.get("/api/notifications/")
        ids = [row["id"] for row in response.data["results"]]
        self.assertEqual(ids, [self.notif_a.id])
