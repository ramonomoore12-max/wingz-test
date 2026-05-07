from django.test import TestCase
from django.utils import timezone

from ride_events.models import RideEvent
from ride_events.serializers import RideEventSerializer
from rides.models import Ride
from rides.serializers import RideSerializer
from users.models import User
from users.serializers import UserSerializer


class SerializerTests(TestCase):
    def setUp(self):
        self.rider = User.objects.create_user(
            email='rider@example.com',
            password='testpass123',
            role='rider',
            first_name='Ride',
            last_name='User',
            phone_number='1111111111',
        )
        self.driver = User.objects.create_user(
            email='driver@example.com',
            password='testpass123',
            role='driver',
            first_name='Drive',
            last_name='User',
            phone_number='2222222222',
        )
        self.ride = Ride.objects.create(
            status='pickup',
            id_rider=self.rider,
            id_driver=self.driver,
            pickup_latitude=37.1,
            pickup_longitude=-122.1,
            dropoff_latitude=37.2,
            dropoff_longitude=-122.2,
            pickup_time=timezone.now(),
        )
        self.event = RideEvent.objects.create(
            id_ride=self.ride,
            description='Status changed to pickup',
        )

    def test_user_serializer_returns_expected_fields(self):
        data = UserSerializer(self.rider).data

        self.assertEqual(
            data,
            {
                'id_user': self.rider.id_user,
                'role': 'rider',
                'first_name': 'Ride',
                'last_name': 'User',
                'email': 'rider@example.com',
                'phone_number': '1111111111',
            },
        )

    def test_ride_event_serializer_returns_expected_fields(self):
        data = RideEventSerializer(self.event).data

        self.assertEqual(data['id_ride_event'], self.event.id_ride_event)
        self.assertEqual(data['id_ride'], self.ride.id_ride)
        self.assertEqual(data['description'], 'Status changed to pickup')
        self.assertIn('created_at', data)

    def test_ride_serializer_nests_users_and_todays_ride_events(self):
        self.ride.todays_ride_events = [self.event]

        data = RideSerializer(self.ride).data

        self.assertEqual(data['id_rider']['email'], self.rider.email)
        self.assertEqual(data['id_driver']['email'], self.driver.email)
        self.assertEqual(len(data['todays_ride_events']), 1)
        self.assertEqual(
            data['todays_ride_events'][0]['id_ride_event'],
            self.event.id_ride_event,
        )
