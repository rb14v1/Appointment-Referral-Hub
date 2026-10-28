from django.conf import settings
from django.db import models


class Patient(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="patient_profile"
    )
    date_of_birth = models.DateField(null=True, blank=True)
    primary_clinic = models.ForeignKey(
        "clinics.Clinic", on_delete=models.SET_NULL, null=True, blank=True, related_name="patients"
    )
    emergency_contact = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.user.get_full_name() or self.user.email
