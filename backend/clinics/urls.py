from rest_framework.routers import DefaultRouter

from clinics.views import ClinicViewSet

router = DefaultRouter()
router.register("clinics", ClinicViewSet, basename="clinic")

urlpatterns = router.urls
