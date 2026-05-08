# Ride Management API

A RESTful API built with Django REST Framework for managing rides, users, and
ride events.

## Setup
### Requirements
- Python 3.14+
- PostgreSQL

### Install
```bash
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

### Environment variables
Create `.env` from `.env.example`:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=ride_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
```

### Database setup
```bash
python manage.py migrate
python manage.py check
```

### Seed sample data
```bash
python manage.py seed_data
```

This creates demo users, rides, ride events, and prints an admin token.

### Run the server
```bash
python manage.py runserver
```

## API Endpoints
### Authentication
`POST /api/token/`

Request body:

```json
{
  "email": "admin@example.com",
  "password": "password123"
}
```

Response:

```json
{
  "token": "your-token",
  "user": {
    "id_user": 1,
    "role": "admin",
    "first_name": "Admin",
    "last_name": "Demo",
    "email": "admin@example.com",
    "phone_number": "555-0001"
  }
}
```

### Resource endpoints
- `GET /api/users/`
- `GET /api/rides/`
- `GET /api/ride-events/`

All resource endpoints use DRF `ModelViewSet`, so they support list, retrieve,
create, update, and delete operations.

### Auth header
```text
Authorization: Token <your-token>
```

### Ride list features
The ride list endpoint supports:

- Pagination:
  `GET /api/rides/?page=2`
- Filter by status:
  `GET /api/rides/?status=en-route`
- Filter by rider email:
  `GET /api/rides/?rider_email=rider@example.com`
- Order by pickup time ascending:
  `GET /api/rides/?ordering=pickup_time`
- Order by pickup time descending:
  `GET /api/rides/?ordering=-pickup_time`
- Sort by nearest pickup location:
  `GET /api/rides/?lat=37.7749&lon=-122.4194`

Paginated response shape:

```json
{
  "count": 100,
  "next": "http://127.0.0.1:8000/api/rides/?page=2",
  "previous": null,
  "results": []
}
```

## Design Decisions
### Custom user model
The project uses `users.User` as `AUTH_USER_MODEL`. This keeps the assessment's
required fields (`role`, `email`, name, phone) on the authenticated user model
itself and makes admin-role checks straightforward.

### Admin-only API access
All resource endpoints use a custom DRF permission class that allows access only
when `request.user.role == 'admin'`.

### Query optimization for the ride list
The ride list is optimized for the assessment requirements:

- `select_related('id_rider', 'id_driver')` loads rider and driver in the main
  ride query.
- `Prefetch(...)` loads only ride events from the last 24 hours into
  `todays_ride_events`.
- This avoids loading the full `ride_event` table for the ride list endpoint.

Expected query pattern for the list endpoint:
- 1 query for ride count used by pagination
- 1 query for rides with rider and driver joins
- 1 query for filtered ride-event prefetch

### Distance sorting
Distance sorting is done in SQL using a Haversine expression through `RawSQL`.
This keeps sorting in the database, so pagination still works correctly.

### Indexes
Indexes were added for the main access patterns:
- `ride.status`
- `ride.pickup_time`
- `ride.id_rider + status`
- `ride_event.id_ride + created_at`
- `user.email` is already indexed because it is `unique=True`

## Testing
Run the test suite with:

```bash
python -m pytest -q
```

Focused test files:

```bash
python -m pytest rides/tests/test_ride_api.py -q
python -m pytest rides/tests/test_query_count.py -q
```

These tests cover:
- admin-only access
- list response shape
- filtering
- ordering
- `todays_ride_events`
- query count for the optimized ride list

## Bonus SQL Report
Returns the count of trips that took more than 1 hour from pickup to dropoff,
grouped by month and driver.

### SQL
```sql
SELECT
    TO_CHAR(pickup_evt.created_at, 'YYYY-MM') AS month,
    u.first_name || ' ' || LEFT(u.last_name, 1) AS driver,
    COUNT(*) AS count_of_trips
FROM ride r
JOIN "user" u
    ON u.id_user = r.id_driver
JOIN ride_event pickup_evt
    ON pickup_evt.id_ride = r.id_ride
   AND pickup_evt.description = 'Status changed to pickup'
JOIN ride_event dropoff_evt
    ON dropoff_evt.id_ride = r.id_ride
   AND dropoff_evt.description = 'Status changed to dropoff'
WHERE
    dropoff_evt.created_at > pickup_evt.created_at
    AND dropoff_evt.created_at - pickup_evt.created_at > INTERVAL '1 hour'
GROUP BY
    TO_CHAR(pickup_evt.created_at, 'YYYY-MM'),
    u.first_name,
    u.last_name
ORDER BY
    month,
    driver;
```

### Logic
- Each completed trip is represented by two rows in `ride_event`: one with
  description `Status changed to pickup` and one with description
  `Status changed to dropoff`.
- The query joins `ride_event` twice for the same ride:
  - once as `pickup_evt`
  - once as `dropoff_evt`
- The trip duration is calculated with:
  `dropoff_evt.created_at - pickup_evt.created_at`
- Only trips longer than 1 hour are counted.
- The result is grouped by:
  - pickup month in `YYYY-MM` format
  - driver name

### Notes
- This query uses the actual table names defined by the models:
  - `ride`
  - `ride_event`
  - `"user"`
- The `dropoff_evt.created_at > pickup_evt.created_at` condition prevents
  negative or invalid durations if event data is inconsistent.
- In a production system with multiple pickup or dropoff events for the same
  ride, a stricter query might be needed to pair the correct events, but this
  version matches the assumptions in the assessment prompt.