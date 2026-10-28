"""
Role + clinic-scoping permission helpers.

The spec requires scoping to happen at the QUERYSET level (not just via
has_permission checks), so that a user literally cannot retrieve another
tenant's rows even by guessing an ID. Each ViewSet mixes in
`ClinicScopedQuerysetMixin` and implements `clinic_ids_for_user` plus
whatever `filter_queryset_for_user` logic it needs; the mixin + role
permission classes below are the shared building blocks.
"""
from rest_framework.permissions import BasePermission


def user_role(request):
    user = getattr(request, "user", None)
    return getattr(user, "role", None)


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and user_role(request) == "admin")


class IsFrontDesk(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and user_role(request) == "front_desk")


class IsClinician(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and user_role(request) == "clinician")


class IsPatientRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and user_role(request) == "patient")


class IsStaff(BasePermission):
    """front_desk, clinician or admin - i.e. not a bare patient."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and user_role(request) in ("front_desk", "clinician", "admin")
        )


def get_staff_clinic_ids(user):
    """Return the set of clinic IDs a front-desk/clinician user is scoped to.

    - front_desk: the single clinic on their User record.
    - clinician: every clinic reachable via their Provider's home clinic AND
      any ProviderClinicAssignment rows (multi-clinic support).
    - admin/patient: not applicable (callers should special-case admin to
      mean "no filtering" and patient to mean "own records only").
    """
    if user.role == "front_desk":
        return {user.clinic_id} if user.clinic_id else set()

    if user.role == "clinician":
        provider = getattr(user, "provider_profile", None)
        if provider is None:
            return set()
        clinic_ids = set(
            provider.clinic_assignments.filter(is_active=True).values_list("clinic_id", flat=True)
        )
        if provider.clinic_id:
            clinic_ids.add(provider.clinic_id)
        return clinic_ids

    return set()


class ClinicScopedQuerysetMixin:
    """Mixin for ViewSets whose queryset must be scoped by role:

    - admin: unrestricted.
    - patient: restricted to rows belonging to the requesting patient.
    - front_desk/clinician: restricted to rows in their assigned clinic(s).

    Subclasses implement `clinic_field` (the ORM lookup from the model to a
    Clinic, e.g. "clinic" or "appointment__clinic") and
    `patient_field` (the lookup to the owning Patient's user, e.g.
    "patient__user").
    """

    clinic_field: str = "clinic"
    patient_field: str = "patient__user"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return qs.none()

        if user.role == "admin":
            return qs

        if user.role == "patient":
            return qs.filter(**{self.patient_field: user})

        clinic_ids = get_staff_clinic_ids(user)
        if not clinic_ids:
            return qs.none()
        return qs.filter(**{f"{self.clinic_field}__in": clinic_ids})
