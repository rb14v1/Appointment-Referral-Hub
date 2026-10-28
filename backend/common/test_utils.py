"""Shared factory helpers for tests (not a Django app - imported directly)."""
from datetime import date, time

from accounts.models import User
from clinics.models import Clinic
from patients.models import Patient
from providers.models import Provider, ProviderAvailability


def make_clinic(name="Clinic A", timezone="UTC", **kwargs):
    return Clinic.objects.create(name=name, timezone=timezone, **kwargs)


def make_user(email, role=User.Role.PATIENT, clinic=None, **kwargs):
    user = User.objects.create_user(email=email, password="testpass123", role=role, clinic=clinic, **kwargs)
    return user


def make_patient(email="patient@example.com", primary_clinic=None):
    user = make_user(email, role=User.Role.PATIENT)
    return Patient.objects.create(user=user, primary_clinic=primary_clinic, date_of_birth=date(1990, 1, 1))


def make_provider(email, home_clinic, specialty="General", slot_duration=30, availability_days=None):
    user = make_user(email, role=User.Role.CLINICIAN)
    provider = Provider.objects.create(user=user, home_clinic=home_clinic, specialty=specialty)
    if availability_days is None:
        availability_days = range(5)  # Mon-Fri
    for day in availability_days:
        ProviderAvailability.objects.create(
            provider=provider,
            clinic=home_clinic,
            recurrence_rule=ProviderAvailability.Recurrence.WEEKLY,
            day_of_week=day,
            start_time=time(9, 0),
            end_time=time(12, 0),
            slot_duration_minutes=slot_duration,
        )
    return provider


def make_front_desk(email, clinic):
    return make_user(email, role=User.Role.FRONT_DESK, clinic=clinic)


def make_admin(email="admin@example.com"):
    return make_user(email, role=User.Role.ADMIN)
