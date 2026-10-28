# Appointment & Referral Hub

Multi-clinic scheduling, provider availability, inter-clinic referrals, and
waitlists. React (Vite + TS) frontend, Django REST Framework backend,
PostgreSQL, Celery/Redis for async work.

## Stack

- Backend: Django 5 + DRF + SimpleJWT, PostgreSQL (exclusion constraint for
  double-booking prevention), Celery + Redis (reminders, waitlist offer
  expiry), django-celery-beat for the periodic schedule.
- Frontend: React 18 + TypeScript + Vite, react-router, axios.

## Running with Docker (recommended)

```
cp .env.example .env
docker compose up --build
docker compose exec backend python manage.py createsuperuser
```

- Backend: http://localhost:8000/api/
- Frontend: http://localhost:5173
- Django admin: http://localhost:8000/admin/

## Running the backend without Docker (dev-only)

Postgres is the only fully supported database (see "Why Postgres" below).
For quick local iteration without Postgres/Docker installed, you can run
against SQLite:

```
cd backend
python -m venv venv
source venv/Scripts/activate   # or venv/bin/activate on macOS/Linux
pip install -r requirements/dev.txt
USE_SQLITE=True python manage.py migrate
USE_SQLITE=True python manage.py test
USE_SQLITE=True python manage.py runserver
```

`USE_SQLITE` is a dev-only escape hatch (see `config/settings/base.py`). It
is NOT part of the supported deployment configuration.

## Running the frontend without Docker

```
cd frontend
npm install
npm run dev
```

## Why Postgres (and what happens without it)

`Appointment` uses a PostgreSQL `ExclusionConstraint` (`btree_gist`) to make
double-booking a provider impossible at the database level, on top of the
application-level `select_for_update()` check in
`appointments/services/booking.py`. The migration that adds this constraint
(`appointments/migrations/0002_overlap_exclusion_constraint.py`) is wrapped
in guarded operation classes (`common/migration_operations.py`) that update
Django's migration state but skip the real DDL on any non-Postgres backend
-- so `migrate`/`test` still succeed on SQLite, just without that specific
guarantee. Always use Postgres in real deployments.

## Key business logic (critical files)

- `backend/appointments/services/booking.py` - transactional booking +
  cancel/check-in/complete/no-show transitions.
- `backend/providers/services/slot_calculator.py` - expands
  `ProviderAvailability` (weekly + one-off rules, blackout overrides) into
  concrete open slots, net of existing appointments.
- `backend/referrals/services/state_machine.py` - explicit referral
  transition map + `transition()` guard.
- `backend/waitlist/tasks.py` - waitlist matching (plain functions, callable
  synchronously or via Celery), offer expiry, decline/expire auto-advance.
- `backend/common/permissions.py` - queryset-level role/clinic scoping used
  by every ViewSet.

## Tests

```
cd backend
USE_SQLITE=True python manage.py test
```

Covers: booking conflict/past/approval-flag rules, slot calculation
(weekly/one-off/blocked), referral state machine (legal + illegal
transitions), waitlist matching (priority, FIFO, decline/expiry
auto-advance), notification idempotency, and at least one cross-tenant
isolation test per app (front-desk at clinic A cannot list/retrieve clinic
B's appointments/availability/referrals/patients/waitlist; a patient cannot
read another patient's records).

## Deviations from a "pure" production setup (documented, not hidden)

- `USE_SQLITE` dev override in settings - for environments without a local
  Postgres/Docker. Never set it outside local dev.
- Celery tasks run with `CELERY_TASK_ALWAYS_EAGER=True` by default (no Redis
  required) unless overridden - docker-compose.yml disables eager mode so
  the real worker/beat processes are exercised.
- Notification "sending" is a logged stub (`notifications/tasks.py::_dispatch`)
  - no real email/SMS provider is wired up.
- Refresh token is stored in `localStorage` rather than an httpOnly cookie,
  since the SPA and API are on different ports/origins in local dev without
  a reverse proxy; documented in `frontend/src/api/client.ts`.
