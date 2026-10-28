from rest_framework.test import APITestCase

from common.test_utils import make_clinic, make_front_desk, make_patient


class PatientIsolationTests(APITestCase):
    def setUp(self):
        self.clinic_a = make_clinic("Clinic A")
        self.clinic_b = make_clinic("Clinic B")
        self.patient_a = make_patient("pat.a@example.com", primary_clinic=self.clinic_a)
        self.patient_b = make_patient("pat.b@example.com", primary_clinic=self.clinic_b)
        self.front_desk_a = make_front_desk("fd.a@example.com", self.clinic_a)

    def test_front_desk_cannot_list_other_clinic_patients(self):
        self.client.force_authenticate(self.front_desk_a)
        response = self.client.get("/api/patients/")
        ids = [row["id"] for row in response.data["results"]]
        self.assertIn(self.patient_a.id, ids)
        self.assertNotIn(self.patient_b.id, ids)

    def test_patient_sees_only_self(self):
        self.client.force_authenticate(self.patient_a.user)
        response = self.client.get("/api/patients/")
        ids = [row["id"] for row in response.data["results"]]
        self.assertEqual(ids, [self.patient_a.id])

    def test_patient_cannot_retrieve_another_patients_record(self):
        self.client.force_authenticate(self.patient_a.user)
        response = self.client.get(f"/api/patients/{self.patient_b.id}/")
        self.assertEqual(response.status_code, 404)
