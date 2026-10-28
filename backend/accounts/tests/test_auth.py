from rest_framework.test import APITestCase

from accounts.models import User
from common.test_utils import make_admin, make_user


class AuthTests(APITestCase):
    def test_register_defaults_to_patient_role(self):
        response = self.client.post(
            "/api/auth/register/",
            {"email": "new@example.com", "password": "StrongPass123!", "first_name": "New"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="new@example.com")
        self.assertEqual(user.role, User.Role.PATIENT)

    def test_register_cannot_self_assign_admin_role(self):
        response = self.client.post(
            "/api/auth/register/",
            {"email": "sneaky@example.com", "password": "StrongPass123!", "role": "admin"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_login_returns_access_and_refresh_tokens(self):
        make_user("login@example.com", role=User.Role.PATIENT)
        response = self.client.post(
            "/api/auth/login/", {"email": "login@example.com", "password": "testpass123"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_non_admin_cannot_list_users(self):
        user = make_user("plain@example.com", role=User.Role.PATIENT)
        self.client.force_authenticate(user)
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, 403)

    def test_admin_can_list_users(self):
        admin = make_admin()
        self.client.force_authenticate(admin)
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, 200)
