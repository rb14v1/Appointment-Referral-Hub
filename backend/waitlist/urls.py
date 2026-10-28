from rest_framework.routers import DefaultRouter

from waitlist.views import WaitlistOfferViewSet, WaitlistViewSet

router = DefaultRouter()
router.register("waitlist", WaitlistViewSet, basename="waitlist")
router.register("waitlist-offers", WaitlistOfferViewSet, basename="waitlist-offer")

urlpatterns = router.urls
