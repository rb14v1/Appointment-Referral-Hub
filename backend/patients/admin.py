from django.contrib import admin

from patients.models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ["user", "primary_clinic", "date_of_birth"]
    search_fields = ["user__email"]
