from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication

from users.permissions import IsAdminRole

from .models import Ride
from .serializers import RideSerializer


class RideViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminRole]
    queryset = Ride.objects.all()
    serializer_class = RideSerializer
