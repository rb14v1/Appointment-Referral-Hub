from django.contrib import admin

from appointments.models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["id", "patient", "provider", "clinic", "start_time", "end_time", "status"]
    list_filter = ["status", "clinic"]
    search_fields = ["patient__user__email", "provider__user__email"]
