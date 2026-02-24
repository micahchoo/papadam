from rest_framework.routers import DefaultRouter

from papadapi.exhibit.views import ExhibitViewSet

router = DefaultRouter(trailing_slash=True)
router.register(r"", ExhibitViewSet, basename="exhibit")

urlpatterns = router.urls
