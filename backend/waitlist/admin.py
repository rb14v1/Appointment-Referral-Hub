from django.contrib import admin

from waitlist.models import Waitlist, WaitlistOffer


@admin.register(Waitlist)
class WaitlistAdmin(admin.ModelAdmin):
    list_display = ["id", "patient", "clinic", "provider", "status", "priority", "created_at"]
    list_filter = ["status", "clinic"]


@admin.register(WaitlistOffer)
class WaitlistOfferAdmin(admin.ModelAdmin):
    list_display = ["id", "waitlist_entry", "provider", "start_time", "response", "expires_at"]
    list_filter = ["response"]
