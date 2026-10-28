from django.contrib import admin

from clinics.models import Clinic


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ["name", "timezone", "is_active", "requires_front_desk_approval"]
    search_fields = ["name"]
