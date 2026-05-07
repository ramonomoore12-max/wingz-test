from rest_framework import serializers

from ride_events.serializers import RideEventSerializer
from users.serializers import UserSerializer

from .models import Ride


class RideSerializer(serializers.ModelSerializer):
    id_rider = UserSerializer(read_only=True)
    id_driver = UserSerializer(read_only=True)
    # Maps to the 'to_attr' set by Prefetch in the ViewSet queryset.
    todays_ride_events = RideEventSerializer(many=True, read_only=True)

    class Meta:
        model = Ride
        fields = [
            'id_ride', 'status',
            'id_rider', 'id_driver',
            'pickup_latitude', 'pickup_longitude',
            'dropoff_latitude', 'dropoff_longitude',
            'pickup_time',
            'todays_ride_events',
        ]
