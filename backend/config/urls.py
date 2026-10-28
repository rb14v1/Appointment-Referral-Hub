from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("accounts.urls")),
    path("api/", include("clinics.urls")),
    path("api/", include("providers.urls")),
    path("api/", include("patients.urls")),
    path("api/", include("appointments.urls")),
    path("api/", include("referrals.urls")),
    path("api/", include("waitlist.urls")),
    path("api/", include("notifications.urls")),
]
