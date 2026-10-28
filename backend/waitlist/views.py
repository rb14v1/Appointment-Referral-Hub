from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from common.permissions import get_staff_clinic_ids
from waitlist.models import Waitlist, WaitlistOffer
from waitlist.serializers import WaitlistOfferResponseSerializer, WaitlistOfferSerializer, WaitlistSerializer
from waitlist.tasks import respond_to_offer


class WaitlistViewSet(viewsets.ModelViewSet):
    queryset = Waitlist.objects.select_related("patient__user", "clinic", "provider__user").all()
    serializer_class = WaitlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "clinic", "provider"]

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
        return qs.filter(clinic_id__in=clinic_ids)

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == "patient":
            from patients.models import Patient

            patient = Patient.objects.filter(user=user).first()
            if patient is None or serializer.validated_data["patient"] != patient:
                raise PermissionDenied("Patients may only join the waitlist for themselves.")
        serializer.save()


class WaitlistOfferViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WaitlistOffer.objects.select_related("waitlist_entry__patient__user", "provider__user").all()
    serializer_class = WaitlistOfferSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["response", "waitlist_entry"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == "admin":
            return qs
        if user.role == "patient":
            return qs.filter(waitlist_entry__patient__user=user)
        clinic_ids = get_staff_clinic_ids(user)
        if not clinic_ids:
            return qs.none()
        return qs.filter(waitlist_entry__clinic_id__in=clinic_ids)

    @action(detail=True, methods=["post"])
    def respond(self, request, pk=None):
        offer = self.get_object()
        user = request.user
        if user.role == "patient" and offer.waitlist_entry.patient.user_id != user.id:
            raise PermissionDenied("You may only respond to your own waitlist offers.")

        serializer = WaitlistOfferResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        accept = serializer.validated_data["accept"]

        if accept:
            from appointments.services.booking import book_appointment

            entry = offer.waitlist_entry
            book_appointment(
                patient=entry.patient,
                provider=offer.provider,
                clinic=entry.clinic,
                start_time=offer.start_time,
                created_by=user,
                slot_duration_minutes=int((offer.end_time - offer.start_time).total_seconds() // 60),
            )

        offer = respond_to_offer(offer, accept=accept)
        return Response(WaitlistOfferSerializer(offer).data)
