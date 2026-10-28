from rest_framework.routers import DefaultRouter

from patients.views import PatientViewSet

router = DefaultRouter()
router.register("patients", PatientViewSet, basename="patient")

urlpatterns = router.urls
