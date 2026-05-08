from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from ride_events.models import RideEvent
from rides.models import Ride
from users.models import User


@pytest.fixture
def admin_client(db):
    admin_user = User.objects.create_user(
        email='admin@test.com',
        password='pw',
        role='admin',
        first_name='Admin',
        last_name='User',
        phone_number='000',
        is_staff=True,
    )
    token, _ = Token.objects.get_or_create(user=admin_user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client, admin_user


@pytest.fixture
def non_admin_client(db):
    rider_user = User.objects.create_user(
        email='rider@test.com',
        password='pw',
        role='rider',
        first_name='Rider',
        last_name='User',
        phone_number='001',
    )
    token, _ = Token.objects.get_or_create(user=rider_user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


@pytest.fixture
def sample_ride(db, admin_client):
    _, admin_user = admin_client
    rider = User.objects.create_user(
        email='jane@test.com',
        password='pw',
        role='rider',
        first_name='Jane',
        last_name='Doe',
        phone_number='111',
    )
    ride = Ride.objects.create(
        status='en-route',
        id_rider=rider,
        id_driver=admin_user,
        pickup_latitude=37.77,
        pickup_longitude=-122.41,
        dropoff_latitude=37.78,
        dropoff_longitude=-122.40,
        pickup_time=timezone.now(),
    )
    return ride


@pytest.mark.django_db
def test_admin_can_access_rides(admin_client, sample_ride):
    client, _ = admin_client
    response = client.get('/api/rides/')

    assert response.status_code == 200


@pytest.mark.django_db
def test_non_admin_is_rejected(non_admin_client, sample_ride):
    response = non_admin_client.get('/api/rides/')

    assert response.status_code == 403


@pytest.mark.django_db
def test_unauthenticated_is_rejected():
    response = APIClient().get('/api/rides/')

    assert response.status_code == 401


@pytest.mark.django_db
def test_ride_list_has_expected_shape(admin_client, sample_ride):
    client, _ = admin_client

    response = client.get('/api/rides/')

    assert response.status_code == 200
    assert 'count' in response.data
    assert 'next' in response.data
    assert 'previous' in response.data
    assert 'results' in response.data

    ride = response.data['results'][0]
    assert 'id_rider' in ride
    assert 'id_driver' in ride
    assert 'todays_ride_events' in ride


@pytest.mark.django_db
def test_filter_by_status(admin_client, sample_ride):
    client, admin_user = admin_client
    other_rider = User.objects.create_user(
        email='other@test.com',
        password='pw',
        role='rider',
        first_name='Other',
        last_name='User',
        phone_number='222',
    )
    Ride.objects.create(
        status='pickup',
        id_rider=other_rider,
        id_driver=admin_user,
        pickup_latitude=37.70,
        pickup_longitude=-122.50,
        dropoff_latitude=37.71,
        dropoff_longitude=-122.49,
        pickup_time=timezone.now(),
    )

    response = client.get('/api/rides/?status=en-route')

    assert response.status_code == 200
    assert response.data['count'] >= 1
    assert all(ride['status'] == 'en-route' for ride in response.data['results'])


@pytest.mark.django_db
def test_filter_by_rider_email(admin_client, sample_ride):
    client, _ = admin_client

    response = client.get('/api/rides/?rider_email=jane@test.com')

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['id_rider']['email'] == 'jane@test.com'


@pytest.mark.django_db
def test_ordering_by_pickup_time(admin_client):
    client, admin_user = admin_client
    rider = User.objects.create_user(
        email='ordered@test.com',
        password='pw',
        role='rider',
        first_name='Ordered',
        last_name='User',
        phone_number='333',
    )
    older_ride = Ride.objects.create(
        status='pickup',
        id_rider=rider,
        id_driver=admin_user,
        pickup_latitude=37.70,
        pickup_longitude=-122.50,
        dropoff_latitude=37.71,
        dropoff_longitude=-122.49,
        pickup_time=timezone.now() - timedelta(hours=2),
    )
    newer_ride = Ride.objects.create(
        status='pickup',
        id_rider=rider,
        id_driver=admin_user,
        pickup_latitude=37.72,
        pickup_longitude=-122.48,
        dropoff_latitude=37.73,
        dropoff_longitude=-122.47,
        pickup_time=timezone.now() - timedelta(hours=1),
    )

    asc_response = client.get('/api/rides/?ordering=pickup_time')
    desc_response = client.get('/api/rides/?ordering=-pickup_time')

    asc_ids = [ride['id_ride'] for ride in asc_response.data['results']]
    desc_ids = [ride['id_ride'] for ride in desc_response.data['results']]

    assert asc_response.status_code == 200
    assert desc_response.status_code == 200
    assert asc_ids.index(older_ride.id_ride) < asc_ids.index(newer_ride.id_ride)
    assert desc_ids.index(newer_ride.id_ride) < desc_ids.index(older_ride.id_ride)


@pytest.mark.django_db
def test_todays_ride_events_within_24h(admin_client, sample_ride):
    client, _ = admin_client
    now = timezone.now()

    recent_event = RideEvent.objects.create(
        id_ride=sample_ride,
        description='Status changed to pickup',
    )
    RideEvent.objects.filter(pk=recent_event.pk).update(
        created_at=now - timedelta(hours=1)
    )

    old_event = RideEvent.objects.create(
        id_ride=sample_ride,
        description='Old event',
    )
    RideEvent.objects.filter(pk=old_event.pk).update(
        created_at=now - timedelta(hours=48)
    )

    response = client.get('/api/rides/')

    ride = next(
        item for item in response.data['results']
        if item['id_ride'] == sample_ride.id_ride
    )
    descriptions = [event['description'] for event in ride['todays_ride_events']]

    assert 'Status changed to pickup' in descriptions
    assert 'Old event' not in descriptions
