from django.contrib import admin

from referrals.models import Referral


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ["id", "patient", "referring_clinic", "receiving_clinic", "status", "urgency", "created_at"]
    list_filter = ["status", "urgency"]
