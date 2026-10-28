from django.contrib import admin

from providers.models import Provider, ProviderAvailability, ProviderClinicAssignment


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ["user", "home_clinic", "specialty", "is_active"]
    search_fields = ["user__email", "specialty"]


@admin.register(ProviderClinicAssignment)
class ProviderClinicAssignmentAdmin(admin.ModelAdmin):
    list_display = ["provider", "clinic", "is_active"]


@admin.register(ProviderAvailability)
class ProviderAvailabilityAdmin(admin.ModelAdmin):
    list_display = ["provider", "clinic", "recurrence_rule", "day_of_week", "specific_date", "start_time", "end_time", "is_blocked"]
    list_filter = ["recurrence_rule", "is_blocked", "clinic"]
