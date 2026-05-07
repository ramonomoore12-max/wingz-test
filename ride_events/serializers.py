from rest_framework import serializers

from .models import RideEvent


class RideEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RideEvent
        fields = [
            'id_ride_event', 'id_ride', 'description', 'created_at',
        ]
