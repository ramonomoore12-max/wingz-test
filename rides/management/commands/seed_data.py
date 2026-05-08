from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from rest_framework.authtoken.models import Token

from ride_events.models import RideEvent
from rides.models import Ride
from users.models import User


class Command(BaseCommand):
    help = 'Seed the database with sample data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=15,
            help='Number of rides to create.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = options['count']
        password = 'password123'
        self.stdout.write('Seeding data...')

        admin_user = self._get_or_update_user(
            email='admin@example.com',
            password=password,
            role='admin',
            first_name='Admin',
            last_name='Demo',
            phone_number='555-0001',
            is_staff=True,
            is_superuser=True,
        )
        rider = self._get_or_update_user(
            email='rider@example.com',
            password=password,
            role='rider',
            first_name='Rider',
            last_name='Demo',
            phone_number='555-0002',
        )
        driver = self._get_or_update_user(
            email='driver@example.com',
            password=password,
            role='driver',
            first_name='Driver',
            last_name='Demo',
            phone_number='555-0003',
        )

        token, _ = Token.objects.get_or_create(user=admin_user)
        self.stdout.write(f'  Admin email: {admin_user.email}')
        self.stdout.write(f'  Admin password: {password}')
        self.stdout.write(f'  Admin token: {token.key}')

        now = timezone.now()
        statuses = [choice for choice, _ in Ride.STATUS_CHOICES]

        for i in range(count):
            ride = Ride.objects.create(
                status=statuses[i % len(statuses)],
                id_rider=rider,
                id_driver=driver,
                pickup_latitude=37.7749 + (i * 0.01),
                pickup_longitude=-122.4194 + (i * 0.01),
                dropoff_latitude=37.7849 + (i * 0.01),
                dropoff_longitude=-122.4094 + (i * 0.01),
                pickup_time=now - timedelta(hours=i),
            )

            pickup_event = RideEvent.objects.create(
                id_ride=ride,
                description='Status changed to pickup',
            )
            RideEvent.objects.filter(pk=pickup_event.pk).update(
                created_at=now - timedelta(hours=i, minutes=30)
            )

            dropoff_event = RideEvent.objects.create(
                id_ride=ride,
                description='Status changed to dropoff',
            )
            RideEvent.objects.filter(pk=dropoff_event.pk).update(
                created_at=now - timedelta(hours=i, minutes=10)
            )

        self.stdout.write(self.style.SUCCESS(f'Created {count} sample rides.'))
        self.stdout.write(self.style.SUCCESS('Seeding complete!'))

    def _get_or_update_user(self, email, password, **extra_fields):
        user, _ = User.objects.get_or_create(
            email=email,
            defaults=extra_fields,
        )

        fields_to_update = []
        for field_name, value in extra_fields.items():
            if getattr(user, field_name) != value:
                setattr(user, field_name, value)
                fields_to_update.append(field_name)

        user.set_password(password)
        fields_to_update.append('password')

        if fields_to_update:
            user.save(update_fields=fields_to_update)

        return user
