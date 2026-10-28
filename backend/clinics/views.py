from rest_framework import permissions, viewsets

from clinics.models import Clinic
from clinics.serializers import ClinicSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


class ClinicViewSet(viewsets.ModelViewSet):
    """Clinics are readable by any authenticated user (patients need the full
    list to pick where to book) but only writable by admins."""

    queryset = Clinic.objects.all().order_by("name")
    serializer_class = ClinicSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["is_active"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == "patient" and self.action == "list":
            return qs.filter(is_active=True)
        return qs
