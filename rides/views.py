from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication

from users.permissions import IsAdminRole

from .filters import RideFilter
from .models import Ride
from .serializers import RideSerializer


class RideViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminRole]
    serializer_class = RideSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RideFilter

    def get_queryset(self):
        return Ride.objects.all()
