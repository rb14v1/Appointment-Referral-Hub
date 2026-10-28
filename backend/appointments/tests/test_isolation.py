from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from appointments.services.booking import book_appointment
from common.test_utils import make_clinic, make_front_desk, make_patient, make_provider


class AppointmentCrossClinicIsolationTests(APITestCase):
    def setUp(self):
        self.clinic_a = make_clinic("Clinic A")
        self.clinic_b = make_clinic("Clinic B")

        self.provider_a = make_provider("doc.a@example.com", self.clinic_a)
        self.provider_b = make_provider("doc.b@example.com", self.clinic_b)

        self.patient_a = make_patient("pat.a@example.com", primary_clinic=self.clinic_a)
        self.patient_b = make_patient("pat.b@example.com", primary_clinic=self.clinic_b)

        self.front_desk_a = make_front_desk("fd.a@example.com", self.clinic_a)

        now = timezone.now()
        days_ahead = (7 - now.weekday()) % 7 or 7
        start = (now + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0, microsecond=0)

        self.appt_a = book_appointment(
            patient=self.patient_a, provider=self.provider_a, clinic=self.clinic_a,
            start_time=start, created_by=self.front_desk_a,
        )
        self.appt_b = book_appointment(
            patient=self.patient_b, provider=self.provider_b, clinic=self.clinic_b,
            start_time=start, created_by=self.front_desk_a,
        )

    def test_front_desk_cannot_list_other_clinics_appointments(self):
        self.client.force_authenticate(self.front_desk_a)
        response = self.client.get("/api/appointments/")
        self.assertEqual(response.status_code, 200)
        ids = [row["id"] for row in response.data["results"]]
        self.assertIn(self.appt_a.id, ids)
        self.assertNotIn(self.appt_b.id, ids)

    def test_front_desk_cannot_retrieve_other_clinics_appointment_by_id(self):
        self.client.force_authenticate(self.front_desk_a)
        response = self.client.get(f"/api/appointments/{self.appt_b.id}/")
        self.assertEqual(response.status_code, 404)

    def test_patient_only_sees_own_appointments(self):
        self.client.force_authenticate(self.patient_a.user)
        response = self.client.get("/api/appointments/")
        ids = [row["id"] for row in response.data["results"]]
        self.assertEqual(ids, [self.appt_a.id])

    def test_patient_cannot_retrieve_other_patients_appointment(self):
        self.client.force_authenticate(self.patient_a.user)
        response = self.client.get(f"/api/appointments/{self.appt_b.id}/")
        self.assertEqual(response.status_code, 404)
