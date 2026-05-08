from datetime import timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from ride_events.models import RideEvent
from rides.models import Ride
from rides.views import RideViewSet
from users.models import User


@pytest.fixture
def setup_data(db):
    admin_user = User.objects.create_user(
        email='qa@test.com',
        password='pw',
        role='admin',
        first_name='QA',
        last_name='Admin',
        phone_number='000',
        is_staff=True,
    )
    rider = User.objects.create_user(
        email='r2@test.com',
        password='pw',
        role='rider',
        first_name='R',
        last_name='R',
        phone_number='111',
    )

    now = timezone.now()
    for i in range(3):
        ride = Ride.objects.create(
            status='en-route',
            id_rider=rider,
            id_driver=admin_user,
            pickup_latitude=37.0 + i,
            pickup_longitude=-122.0 - i,
            dropoff_latitude=37.1 + i,
            dropoff_longitude=-122.1 - i,
            pickup_time=now - timedelta(hours=i),
        )
        recent_event = RideEvent.objects.create(
            id_ride=ride,
            description='Status changed to pickup',
        )
        RideEvent.objects.filter(pk=recent_event.pk).update(
            created_at=now - timedelta(hours=1)
        )

        old_event = RideEvent.objects.create(
            id_ride=ride,
            description='Old event',
        )
        RideEvent.objects.filter(pk=old_event.pk).update(
            created_at=now - timedelta(hours=48)
        )

    factory = APIRequestFactory()
    request = factory.get('/api/rides/')
    force_authenticate(request, user=admin_user)
    view = RideViewSet.as_view({'get': 'list'})
    return request, view


@pytest.mark.django_db
def test_ride_list_uses_exactly_3_queries(setup_data):
    request, view = setup_data

    with CaptureQueriesContext(connection) as ctx:
        response = view(request)

    assert response.status_code == 200
    assert len(ctx.captured_queries) == 3, (
        f'Expected exactly 3 queries, got {len(ctx.captured_queries)}:\n'
        + '\n'.join(query['sql'] for query in ctx.captured_queries)
    )


@pytest.mark.django_db
def test_full_ride_event_table_never_loaded(setup_data):
    request, view = setup_data

    with CaptureQueriesContext(connection) as ctx:
        response = view(request)

    assert response.status_code == 200

    ride_event_queries = [
        query['sql'].upper()
        for query in ctx.captured_queries
        if 'RIDE_EVENT' in query['sql'].upper()
    ]

    assert ride_event_queries, 'Expected a RideEvent prefetch query.'

    for sql in ride_event_queries:
        assert 'WHERE' in sql, (
            'RideEvent query has no WHERE clause and may load the full table.'
        )
        assert 'CREATED_AT' in sql, (
            'RideEvent query is missing the last-24h created_at filter.'
        )
        assert 'ID_RIDE' in sql, (
            'RideEvent query is missing the ride ID constraint for prefetching.'
        )
