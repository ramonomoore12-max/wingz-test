from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication

from users.permissions import IsAdminRole

from .models import RideEvent
from .serializers import RideEventSerializer


class RideEventViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminRole]
    queryset = RideEvent.objects.all()
    serializer_class = RideEventSerializer
