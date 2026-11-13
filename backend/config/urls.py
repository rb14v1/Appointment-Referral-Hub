from django.contrib import admin
from django.urls import include, path
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthzView(APIView):
    """Unauthenticated liveness probe for orchestrators and load balancers."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"})


urlpatterns = [
    path("healthz", HealthzView.as_view(), name="healthz"),
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
