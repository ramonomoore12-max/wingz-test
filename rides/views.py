from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.expressions import RawSQL
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.filters import OrderingFilter

from users.permissions import IsAdminRole

from .filters import RideFilter
from .models import Ride
from .serializers import RideSerializer

HAVERSINE_SQL = """
    6371 * acos(
        LEAST(1.0,
            cos(radians(%s)) * cos(radians(pickup_latitude))
            * cos(radians(pickup_longitude) - radians(%s))
            + sin(radians(%s)) * sin(radians(pickup_latitude))
        )
    )
"""


class RideViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminRole]
    serializer_class = RideSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = RideFilter
    ordering_fields = ['pickup_time']
    ordering = ['pickup_time']

    def get_queryset(self):
        qs = Ride.objects.all()

        lat = self.request.query_params.get('lat')
        lon = self.request.query_params.get('lon')

        if lat and lon:
            try:
                lat, lon = float(lat), float(lon)
                qs = qs.annotate(
                    distance=RawSQL(HAVERSINE_SQL, (lat, lon, lat))
                ).order_by('distance')
            except (TypeError, ValueError):
                pass

        return qs
