from rest_framework.test import APITestCase

from common.test_utils import make_clinic, make_front_desk, make_patient, make_provider
from referrals.models import Referral


class ReferralCrossClinicIsolationTests(APITestCase):
    def setUp(self):
        self.clinic_a = make_clinic("Clinic A")
        self.clinic_b = make_clinic("Clinic B")
        self.clinic_c = make_clinic("Clinic C")

        self.provider_a = make_provider("doc.a@example.com", self.clinic_a)
        self.patient = make_patient("pat@example.com", primary_clinic=self.clinic_a)
        self.front_desk_c = make_front_desk("fd.c@example.com", self.clinic_c)

        self.referral = Referral.objects.create(
            patient=self.patient,
            referring_clinic=self.clinic_a,
            referring_provider=self.provider_a,
            receiving_clinic=self.clinic_b,
            reason="Needs specialist",
        )

    def test_unrelated_clinic_staff_cannot_see_referral(self):
        self.client.force_authenticate(self.front_desk_c)
        response = self.client.get("/api/referrals/")
        ids = [row["id"] for row in response.data["results"]]
        self.assertNotIn(self.referral.id, ids)

    def test_unrelated_clinic_staff_cannot_accept_referral(self):
        self.client.force_authenticate(self.front_desk_c)
        response = self.client.post(f"/api/referrals/{self.referral.id}/accept/", {}, format="json")
        self.assertIn(response.status_code, (403, 404))
