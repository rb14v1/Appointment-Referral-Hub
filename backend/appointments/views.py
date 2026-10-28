from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from appointments.models import Appointment
from appointments.serializers import (
    AppointmentSerializer,
    BookAppointmentSerializer,
    CancelAppointmentSerializer,
)
from appointments.services.booking import (
    book_appointment,
    cancel_appointment,
    check_in_appointment,
    complete_appointment,
    mark_no_show,
)
from clinics.models import Clinic
from common.permissions import ClinicScopedQuerysetMixin
from patients.models import Patient
from providers.models import Provider


class AppointmentViewSet(ClinicScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Appointment.objects.select_related("patient__user", "provider__user", "clinic").all()
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "provider", "clinic", "patient"]
    clinic_field = "clinic"
    patient_field = "patient__user"

    def create(self, request, *args, **kwargs):
        serializer = BookAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        try:
            patient = Patient.objects.get(id=data["patient"])
            provider = Provider.objects.get(id=data["provider"])
            clinic = Clinic.objects.get(id=data["clinic"])
        except (Patient.DoesNotExist, Provider.DoesNotExist, Clinic.DoesNotExist) as exc:
            raise ValidationError(str(exc))

        if user.role == "patient" and patient.user_id != user.id:
            raise PermissionDenied("Patients may only book appointments for themselves.")

        if user.role in ("front_desk",) and user.clinic_id != clinic.id:
            raise PermissionDenied("Front desk may only book within their own clinic.")

        referral = None
        if data.get("referral"):
            from referrals.models import Referral

            referral = Referral.objects.filter(id=data["referral"]).first()

        appointment = book_appointment(
            patient=patient,
            provider=provider,
            clinic=clinic,
            start_time=data["start_time"],
            reason=data.get("reason", ""),
            created_by=user,
            referral=referral,
        )
        return Response(AppointmentSerializer(appointment).data, status=201)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        serializer = CancelAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = cancel_appointment(appointment, actor=request.user, reason=serializer.validated_data.get("reason", ""))
        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["post"], url_path="check-in")
    def check_in(self, request, pk=None):
        appointment = self.get_object()
        appointment = check_in_appointment(appointment)
        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        appointment = self.get_object()
        appointment = complete_appointment(appointment)
        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["post"], url_path="no-show")
    def no_show(self, request, pk=None):
        appointment = self.get_object()
        appointment = mark_no_show(appointment)
        return Response(AppointmentSerializer(appointment).data)
