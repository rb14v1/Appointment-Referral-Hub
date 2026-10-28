from django.contrib.auth.models import AbstractUser
from django.db import models

from accounts.managers import UserManager


class User(AbstractUser):
    class Role(models.TextChoices):
        PATIENT = "patient", "Patient"
        FRONT_DESK = "front_desk", "Front Desk"
        CLINICIAN = "clinician", "Clinician"
        ADMIN = "admin", "Admin"

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PATIENT)
    # Only meaningful for role=front_desk: scopes a front-desk user to a
    # single home clinic. Clinicians use ProviderClinicAssignment instead
    # (a provider can work at multiple clinics).
    clinic = models.ForeignKey(
        "clinics.Clinic",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="front_desk_staff",
    )
    phone = models.CharField(max_length=32, blank=True, default="")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"
