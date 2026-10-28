from datetime import timedelta

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from providers.models import Provider, ProviderAvailability, ProviderClinicAssignment
from providers.serializers import (
    ProviderAvailabilitySerializer,
    ProviderClinicAssignmentSerializer,
    ProviderSerializer,
    SlotQuerySerializer,
    SlotSerializer,
)
from providers.services.slot_calculator import get_available_slots


class IsAdminOrSelfClinician(permissions.BasePermission):
    """Admins can manage any provider/availability row. A clinician can only
    write their own. Everyone authenticated can read (needed to browse
    providers/slots when booking)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.role == "admin":
            return True
        provider = obj if isinstance(obj, Provider) else obj.provider
        return request.user.role == "clinician" and provider.user_id == request.user.id


class ProviderViewSet(viewsets.ModelViewSet):
    queryset = Provider.objects.select_related("user", "home_clinic").all()
    serializer_class = ProviderSerializer
    permission_classes = [IsAdminOrSelfClinician]
    filterset_fields = ["home_clinic", "specialty", "is_active"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == "front_desk" and user.clinic_id:
            qs = qs.filter(
                models_q_clinic(user.clinic_id)
            )
        return qs

    @action(detail=True, methods=["get"])
    def slots(self, request, pk=None):
        provider = self.get_object()
        query = SlotQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)

        clinic = None
        clinic_id = query.validated_data.get("clinic")
        if clinic_id:
            clinic = provider.home_clinic if provider.home_clinic_id == clinic_id else None
            if clinic is None:
                from clinics.models import Clinic
                clinic = Clinic.objects.filter(id=clinic_id).first()

        slots = get_available_slots(
            provider,
            query.validated_data["date_from"],
            query.validated_data["date_to"],
            clinic=clinic,
        )
        data = [
            {
                "provider": provider.id,
                "clinic": slot.clinic_id,
                "start_time": slot.start,
                "end_time": slot.end,
            }
            for slot in slots
        ]
        return Response(SlotSerializer(data, many=True).data)


def models_q_clinic(clinic_id):
    from django.db.models import Q
    return Q(home_clinic_id=clinic_id) | Q(clinic_assignments__clinic_id=clinic_id, clinic_assignments__is_active=True)


class ProviderAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = ProviderAvailability.objects.select_related("provider", "clinic").all()
    serializer_class = ProviderAvailabilitySerializer
    permission_classes = [IsAdminOrSelfClinician]
    filterset_fields = ["provider", "clinic", "recurrence_rule", "is_blocked"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == "admin":
            return qs
        if user.role == "clinician":
            provider = getattr(user, "provider_profile", None)
            return qs.filter(provider=provider) if provider else qs.none()
        if user.role == "front_desk" and user.clinic_id:
            return qs.filter(clinic_id=user.clinic_id)
        # patients can view availability (read-only, to help pick a slot)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == "clinician":
            provider = getattr(user, "provider_profile", None)
            if provider is None or serializer.validated_data.get("provider") != provider:
                raise PermissionDenied("Clinicians may only create availability for themselves.")
        serializer.save()


class ProviderClinicAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ProviderClinicAssignment.objects.select_related("provider", "clinic").all()
    serializer_class = ProviderClinicAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.role == "admin":
            return qs
        if user.role == "clinician":
            provider = getattr(user, "provider_profile", None)
            return qs.filter(provider=provider) if provider else qs.none()
        return qs.none()
