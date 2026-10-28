from rest_framework import permissions, viewsets

from common.permissions import get_staff_clinic_ids
from patients.models import Patient
from patients.serializers import PatientSerializer


class PatientViewSet(viewsets.ModelViewSet):
    """Patients can see/edit only their own profile. Staff are scoped to
    patients whose primary_clinic matches their clinic(s). Admin sees all."""

    queryset = Patient.objects.select_related("user", "primary_clinic").all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["primary_clinic"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == "admin":
            return qs
        if user.role == "patient":
            return qs.filter(user=user)
        clinic_ids = get_staff_clinic_ids(user)
        if not clinic_ids:
            return qs.none()
        return qs.filter(primary_clinic_id__in=clinic_ids)
