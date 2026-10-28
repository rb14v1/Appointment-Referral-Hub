from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from common.test_utils import make_clinic, make_front_desk, make_patient
from waitlist.models import Waitlist


class WaitlistIsolationTests(APITestCase):
    def setUp(self):
        self.clinic_a = make_clinic("Clinic A")
        self.clinic_b = make_clinic("Clinic B")
        self.patient_a = make_patient("pat.a@example.com", primary_clinic=self.clinic_a)
        self.patient_b = make_patient("pat.b@example.com", primary_clinic=self.clinic_b)
        self.front_desk_a = make_front_desk("fd.a@example.com", self.clinic_a)

        now = timezone.now()
        self.entry_a = Waitlist.objects.create(
            patient=self.patient_a, clinic=self.clinic_a,
            desired_date_range_start=now.date(), desired_date_range_end=(now + timedelta(days=30)).date(),
        )
        self.entry_b = Waitlist.objects.create(
            patient=self.patient_b, clinic=self.clinic_b,
            desired_date_range_start=now.date(), desired_date_range_end=(now + timedelta(days=30)).date(),
        )

    def test_front_desk_only_sees_own_clinic_waitlist(self):
        self.client.force_authenticate(self.front_desk_a)
        response = self.client.get("/api/waitlist/")
        ids = [row["id"] for row in response.data["results"]]
        self.assertIn(self.entry_a.id, ids)
        self.assertNotIn(self.entry_b.id, ids)

    def test_patient_cannot_see_other_patients_waitlist_entry(self):
        self.client.force_authenticate(self.patient_a.user)
        response = self.client.get(f"/api/waitlist/{self.entry_b.id}/")
        self.assertEqual(response.status_code, 404)
