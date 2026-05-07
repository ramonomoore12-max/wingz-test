from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ride_events.views import RideEventViewSet
from rides.views import RideViewSet
from users.views import AdminTokenView, UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'rides', RideViewSet, basename='ride')
router.register(r'ride-events', RideEventViewSet, basename='rideevent')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', AdminTokenView.as_view(), name='api-token'),
    path('api/', include(router.urls)),
]
