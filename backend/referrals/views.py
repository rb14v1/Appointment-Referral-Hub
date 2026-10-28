from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from common.permissions import get_staff_clinic_ids
from providers.models import Provider
from referrals.models import Referral
from referrals.serializers import (
    ReferralAcceptSerializer,
    ReferralRejectSerializer,
    ReferralScheduleSerializer,
    ReferralSerializer,
)
from referrals.services import state_machine


class ReferralViewSet(viewsets.ModelViewSet):
    queryset = Referral.objects.select_related(
        "patient__user", "referring_clinic", "receiving_clinic", "referring_provider", "receiving_provider"
    ).all()
    serializer_class = ReferralSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "urgency", "referring_clinic", "receiving_clinic"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == "admin":
            return qs
        if user.role == "patient":
            return qs.filter(patient__user=user)
        clinic_ids = get_staff_clinic_ids(user)
        if not clinic_ids:
            return qs.none()
        # Staff see referrals where their clinic is on EITHER side (sent or received).
        return qs.filter(Q(referring_clinic_id__in=clinic_ids) | Q(receiving_clinic_id__in=clinic_ids))

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def _ensure_receiving_clinic_staff(self, referral):
        user = self.request.user
        if user.role == "admin":
            return
        if user.role in ("front_desk", "clinician"):
            if referral.receiving_clinic_id in get_staff_clinic_ids(user):
                return
        raise PermissionDenied("Only staff at the receiving clinic can act on this referral.")

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        referral = self.get_object()
        self._ensure_receiving_clinic_staff(referral)
        serializer = ReferralAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        receiving_provider = None
        provider_id = serializer.validated_data.get("receiving_provider")
        if provider_id:
            receiving_provider = Provider.objects.filter(id=provider_id).first()

        referral = state_machine.accept(
            referral,
            actor=request.user,
            receiving_provider=receiving_provider,
            notes=serializer.validated_data.get("notes"),
        )
        return Response(ReferralSerializer(referral).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        referral = self.get_object()
        self._ensure_receiving_clinic_staff(referral)
        serializer = ReferralRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        referral = state_machine.reject(referral, actor=request.user, notes=serializer.validated_data.get("notes"))
        return Response(ReferralSerializer(referral).data)

    @action(detail=True, methods=["post"])
    def schedule(self, request, pk=None):
        """Accept -> schedule: books the appointment at the receiving clinic
        and advances the referral to 'scheduled' atomically with it."""
        referral = self.get_object()
        self._ensure_receiving_clinic_staff(referral)
        serializer = ReferralScheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            provider = Provider.objects.get(id=data["provider"])
        except Provider.DoesNotExist:
            raise ValidationError("Provider not found.")

        from appointments.services.booking import book_appointment

        appointment = book_appointment(
            patient=referral.patient,
            provider=provider,
            clinic=referral.receiving_clinic,
            start_time=data["start_time"],
            reason=data.get("reason") or referral.reason,
            created_by=request.user,
            referral=referral,
        )
        referral = state_machine.mark_scheduled(referral, actor=request.user)

        from appointments.serializers import AppointmentSerializer

        return Response(
            {
                "referral": ReferralSerializer(referral).data,
                "appointment": AppointmentSerializer(appointment).data,
            }
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        referral = self.get_object()
        user = request.user
        is_patient_owner = user.role == "patient" and referral.patient.user_id == user.id
        is_staff_side = user.role in ("front_desk", "clinician", "admin") and (
            user.role == "admin"
            or referral.referring_clinic_id in get_staff_clinic_ids(user)
            or referral.receiving_clinic_id in get_staff_clinic_ids(user)
        )
        if not (is_patient_owner or is_staff_side):
            raise PermissionDenied("Not authorized to cancel this referral.")
        referral = state_machine.cancel(referral, actor=user)
        return Response(ReferralSerializer(referral).data)
