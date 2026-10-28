from rest_framework.test import APITestCase

from common.test_utils import make_clinic, make_front_desk, make_provider


class ProviderAvailabilityIsolationTests(APITestCase):
    def setUp(self):
        self.clinic_a = make_clinic("Clinic A")
        self.clinic_b = make_clinic("Clinic B")
        self.provider_a = make_provider("doc.a@example.com", self.clinic_a)
        self.provider_b = make_provider("doc.b@example.com", self.clinic_b)
        self.front_desk_a = make_front_desk("fd.a@example.com", self.clinic_a)

    def test_front_desk_cannot_list_other_clinics_availability(self):
        self.client.force_authenticate(self.front_desk_a)
        response = self.client.get("/api/availability/")
        self.assertEqual(response.status_code, 200)
        clinic_ids = {row["clinic"] for row in response.data["results"]}
        self.assertEqual(clinic_ids, {self.clinic_a.id})

    def test_clinician_cannot_edit_another_clinicians_availability(self):
        other_availability = self.provider_b.availability_blocks.first()
        self.client.force_authenticate(self.provider_a.user)
        response = self.client.patch(
            f"/api/availability/{other_availability.id}/", {"slot_duration_minutes": 15}, format="json"
        )
        self.assertIn(response.status_code, (403, 404))
