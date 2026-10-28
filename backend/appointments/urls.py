from rest_framework.routers import DefaultRouter

from appointments.views import AppointmentViewSet

router = DefaultRouter()
router.register("appointments", AppointmentViewSet, basename="appointment")

urlpatterns = router.urls
