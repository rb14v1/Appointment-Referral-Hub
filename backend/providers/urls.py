from rest_framework.routers import DefaultRouter

from providers.views import ProviderAvailabilityViewSet, ProviderClinicAssignmentViewSet, ProviderViewSet

router = DefaultRouter()
router.register("providers", ProviderViewSet, basename="provider")
router.register("availability", ProviderAvailabilityViewSet, basename="availability")
router.register("provider-clinic-assignments", ProviderClinicAssignmentViewSet, basename="provider-clinic-assignment")

urlpatterns = router.urls
