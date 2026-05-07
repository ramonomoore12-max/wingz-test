from django.db import models

from rides.models import Ride


class RideEvent(models.Model):
    id_ride_event = models.AutoField(primary_key=True)
    id_ride = models.ForeignKey(
        Ride,
        related_name='ride_events',
        on_delete=models.CASCADE,
        db_column='id_ride',
    )
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ride_event'

    def __str__(self):
        return f'Event {self.id_ride_event} on Ride {self.id_ride_id}'
