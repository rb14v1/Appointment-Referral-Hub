from rest_framework.test import APITestCase

from common.test_utils import make_admin, make_clinic, make_front_desk


class ClinicPermissionTests(APITestCase):
    def setUp(self):
        self.clinic = make_clinic("Clinic A")
        self.admin = make_admin()
        self.front_desk = make_front_desk("fd@example.com", self.clinic)

    def test_any_authenticated_user_can_list_clinics(self):
        self.client.force_authenticate(self.front_desk)
        response = self.client.get("/api/clinics/")
        self.assertEqual(response.status_code, 200)

    def test_non_admin_cannot_create_clinic(self):
        self.client.force_authenticate(self.front_desk)
        response = self.client.post("/api/clinics/", {"name": "New Clinic", "timezone": "UTC"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_clinic(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post("/api/clinics/", {"name": "New Clinic", "timezone": "UTC"}, format="json")
        self.assertEqual(response.status_code, 201)
