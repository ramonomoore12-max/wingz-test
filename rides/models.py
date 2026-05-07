from django.db import models

from users.models import User


class Ride(models.Model):
    STATUS_CHOICES = [
        ('en-route', 'En Route'),
        ('pickup', 'Pickup'),
        ('dropoff', 'Dropoff'),
    ]

    id_ride = models.AutoField(primary_key=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    id_rider = models.ForeignKey(
        User,
        related_name='rides_as_rider',
        on_delete=models.CASCADE,
        db_column='id_rider',
    )
    id_driver = models.ForeignKey(
        User,
        related_name='rides_as_driver',
        on_delete=models.CASCADE,
        db_column='id_driver',
    )
    pickup_latitude = models.FloatField()
    pickup_longitude = models.FloatField()
    dropoff_latitude = models.FloatField()
    dropoff_longitude = models.FloatField()
    pickup_time = models.DateTimeField()

    class Meta:
        db_table = 'ride'

    def __str__(self):
        return f'Ride {self.id_ride} [{self.status}]'
