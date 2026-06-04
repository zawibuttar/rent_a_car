# RentACar

A full-stack **peer-to-peer car rental** platform. Owners list vehicles; customers browse, request bookings, and leave reviews. Platform admins moderate listings and owners, and oversee bookings.

Built with **Django 6**, **Django REST Framework**, **PostgreSQL**, optional **Redis** caching, and a **server-rendered UI** (templates + vanilla JavaScript) with light/dark theme support.

---

## Table of contents

- [Product overview](#product-overview)
- [Product requirements](#product-requirements)
- [User roles & capabilities](#user-roles--capabilities)
- [Business rules](#business-rules)
- [Public pages & dashboards](#public-pages--dashboards)
- [Tech stack](#tech-stack)
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [API overview](#api-overview)
- [Project structure](#project-structure)
- [Development notes](#development-notes)

---

## Product overview

RentACar connects **car owners** who want to rent out vehicles with **customers** who need short-term rentals. The platform provides:

- A searchable public catalog of available cars
- Booking requests with owner approval workflow
- Role-specific dashboards (customer, owner, admin)
- Optional admin moderation (hide listings, verify owners)

There is **no payment gateway** in the current release—pricing is calculated and displayed; payment is assumed offline.

---

## Product requirements

### Goals

| Goal | Description |
|------|-------------|
| **Discover** | Customers can search, filter, and paginate live listings. |
| **List** | Owners can publish cars that appear on Browse without a manual approval queue. |
| **Book** | Customers submit date-range requests; owners approve or reject. |
| **Operate** | Admins monitor cars, bookings, and owner verification status. |
| **Trust** | Reviews after completed bookings; owner profiles can be verified by admin. |

### Functional requirements

#### Authentication & accounts

- [x] Register as **Customer** or **Owner** only (admin accounts cannot self-register via API).
- [x] Login / logout with **token authentication** (stored in browser `localStorage`).
- [x] Session-friendly API for same-origin browser use.
- [x] Change password (invalidates token).
- [x] Customer profile: phone, national ID, profile picture.
- [x] Owner profile: phone, business info, profile picture; **admin can verify** owners.

#### Cars & listings

- [x] Owner creates listing: brand, model, year, type, description, location, price/day, images.
- [x] New listings are **`is_approved=True` by default** and appear on Browse when **`is_available=True`**.
- [x] Owner can edit, toggle availability, upload/delete images, delete listing.
- [x] Public catalog shows only **approved + available** cars.
- [x] Car detail page with gallery, specs, booking CTA (customers only).
- [x] Admin can **hide** listing (`is_approved=false`) or **restore** (`is_approved=true`).

#### Bookings

- [x] Customer creates booking: car, start/end dates, optional note.
- [x] Total cost = days × `price_per_day` (end date must be after start).
- [x] Status flow: `pending` → `approved` / `rejected`; customer can **cancel** while pending/approved; owner can **complete** approved bookings.
- [x] Customer **review** (rating 1–5 + comment) after **completed** booking.

#### Admin

- [x] Overview stats: cars, bookings, owners, revenue-style totals from bookings.
- [x] Tables: all cars (with hide/restore), all bookings, all owners (verify/revoke).
- [x] Django admin site at `/admin/` for superusers.

#### UI / UX

- [x] Responsive layout; Inter typography; SVG icon system (no emoji UI).
- [x] Light / dark theme (persisted in `localStorage`).
- [x] Listing cards on Home and Browse (image, type, availability, price, CTA).
- [x] **Pagination**: server-side on catalog (12/page); client-side on large dashboard tables.
- [x] Empty states, loading spinners, toast notifications.

#### Performance & caching

- [x] Public car list/detail: **no browser HTTP cache** on `/api/cars/` (fresh browse after new listings).
- [x] Optional **Redis** cache for admin list endpoints when `CACHE_ENABLED=1`.
- [x] Cache invalidation on car/booking/profile writes via Django signals.

### Non-functional requirements

| Area | Requirement |
|------|-------------|
| **Security** | Role-based API permissions; registration limited to customer/owner; password validators; API throttling on auth/booking; XSS-safe UI escaping for API-driven HTML. |
| **Data** | PostgreSQL in production/Docker; SQLite possible for local dev without Docker DB. |
| **Deploy** | Docker Compose: `web` + `postgres` + `redis`; Gunicorn + Whitenoise for static files. |
| **Media** | Car and profile images under `MEDIA_ROOT` (volume mount in Docker). |

### Out of scope (current version)

- Online payments (Stripe, etc.)
- Email/SMS notifications
- Real-time chat between customer and owner
- GPS / delivery tracking
- Multi-language (i18n)
- Mobile native apps

---

## User roles & capabilities

### Customer

- Browse and search cars (guest or logged in).
- Book cars; view/cancel own bookings.
- Submit reviews after completed trips.
- Manage customer profile.

### Owner

- All customer-facing browse (cannot book own cars via customer flow).
- Publish and manage own listings (instant go-live).
- Approve/reject booking requests; mark approved bookings complete.
- Manage owner profile; subject to admin verification badge.

### Admin (platform)

- View platform-wide cars, bookings, owners.
- Hide or restore listings on the marketplace.
- Verify or revoke owner profiles.
- Update booking status via admin API (moderation).

---

## Business rules

### Listing visibility (Browse Cars)

A car appears on **Home** and **Browse** (`GET /api/cars/`) only when:

```
is_approved = True  AND  is_available = True
```

- **On create**: `is_approved` defaults to `True` (no admin approval step required to go live).
- **Owner** can set `is_available=False` to hide from browse without deleting.
- **Admin** can set `is_approved=False` to remove from browse (moderation).

### Booking lifecycle

```
pending ──(owner approve)──► approved ──(owner complete)──► completed
   │                              │
   ├──(owner reject)──► rejected   └──(customer cancel)──► cancelled
   └──(customer cancel)──► cancelled
```

- Reviews are allowed only for **completed** bookings (one review per booking).

### Pricing & rental types

Each listing can offer one or more of **hourly**, **daily**, **weekly**, and **monthly** rentals, with separate owner-set prices (`price_per_hour`, `price_per_day`, `price_per_week`, `price_per_month`). Bookings store `rental_type`, `start_at`, and `end_at` (ISO datetimes). The API recomputes `total_cost` server-side (`bookings/pricing.py`).

| Type | Rules | Billing |
|------|--------|---------|
| **Hourly** | Return after pick-up; minimum 1 hour; cost pro-rated by actual elapsed time | `elapsed_hours × price_per_hour` |
| **Daily** | Same calendar day allowed; return on or after pick-up | **Inclusive** days: `(end date − start date) + 1`, minimum 1 × `price_per_day` |
| **Weekly** | Minimum 7 inclusive calendar days | `ceil(days / 7) × price_per_week` |
| **Monthly** | Minimum 30 inclusive calendar days | `ceil(days / 30) × price_per_month` |

**Overlap:** Pending and approved bookings block overlapping datetime intervals. Daily (and weekly/monthly) bookings normalize to full calendar days in the listing timezone, so a daily rental blocks entire days. Hourly bookings use exact times; enabling both hourly and daily on one car can allow conflicts unless daily bookings already cover those days—owners should enable both only when they understand this.

---

## Public pages & dashboards

| URL | Description |
|-----|-------------|
| `/` | Home — hero search, filters, paginated listing grid |
| `/cars/` | Browse Cars — search, filters, sort, pagination |
| `/cars/<id>/` | Car detail — gallery, book modal (customers) |
| `/login/` | Login |
| `/register/` | Register (customer or owner) |
| `/dashboard/customer/` | Customer dashboard |
| `/dashboard/owner/` | Owner dashboard |
| `/dashboard/admin/` | Admin dashboard |
| `/admin/` | Django admin |

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Backend | Django 6, Django REST Framework, django-filter |
| Database | PostgreSQL 16 (Docker) / SQLite (local fallback) |
| Cache | Redis 7 (optional), LocMem fallback |
| Auth | DRF Token Authentication |
| Frontend | Django templates, CSS design system, `api.js` + `ui.js` |
| Server | Gunicorn, Whitenoise |
| Containers | Docker Compose |

---

## Getting started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose, **or**
- Python 3.12+, PostgreSQL (optional), Redis (optional)

### Run with Docker (recommended)

```bash
git clone <your-repo-url>
cd rent_a_car

docker compose up --build
```

- App: **http://localhost:8002** (mapped from container port 8000)
- Migrations run automatically on startup.

Create a superuser (optional, for Django admin):

```bash
docker compose exec web python manage.py createsuperuser
```

Collect static files after CSS/JS changes:

```bash
docker compose run --rm web python manage.py collectstatic --noinput
```

### Run locally (without Docker)

```bash
cd rent_a_car
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cd rentacar
python manage.py migrate
python manage.py runserver
```

Open **http://127.0.0.1:8000/**. Uses SQLite by default unless `DB_*` env vars point to PostgreSQL.

---

## Configuration

Environment variables (see `docker-compose.yml` for examples):

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret (**required** when `DEBUG=0`) | dev-only key in compose |
| `DEBUG` | Debug mode (`1`/`0`) | `1` in compose |
| `ALLOWED_HOSTS` | Comma-separated hosts | `127.0.0.1,localhost` |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated origins (HTTPS deploy) | empty |
| `DB_ENGINE` | Database backend | PostgreSQL in Docker |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | DB connection | compose values |
| `REDIS_URL` | Redis URL | `redis://redis:6379/1` |
| `CACHE_ENABLED` | `1` enables Redis list cache for admin APIs | `1` in compose |
| `CACHE_TTL_ADMIN_LIST` | Admin list cache TTL (seconds) | `120` |
| `THROTTLE_ANON`, `THROTTLE_USER`, `THROTTLE_AUTH`, `THROTTLE_BOOKING` | DRF rate limits | see `settings.py` |
| `CAR_IMAGE_MAX_BYTES`, `CAR_IMAGE_MAX_COUNT` | Upload limits | 5MB, 10 images |

DRF pagination: **`PAGE_SIZE = 12`** for list APIs (public catalog, dashboards use `API.fetchAllPages()` in the browser to load all pages). Health check: **`GET /api/health/`**.

### Admin accounts

Platform **admin** users are not created through public registration. Use Django `createsuperuser`, assign `role=admin` in the database, or use the Django admin site.

---

## API overview

Base path: `/api/`. Authenticated requests: header `Authorization: Token <token>`.

### Accounts (`/api/accounts/`)

| Method | Endpoint | Access |
|--------|----------|--------|
| POST | `register/` | Public |
| POST | `login/` | Public |
| POST | `logout/` | Auth |
| GET | `me/` | Auth |
| GET/PATCH | `profile/customer/` | Customer |
| GET/PATCH | `profile/owner/` | Owner |
| POST | `change-password/` | Auth |
| GET | `admin/owners/` | Admin |
| PATCH | `admin/owners/<id>/verify/` | Admin |

### Cars (`/api/cars/`)

| Method | Endpoint | Access |
|--------|----------|--------|
| GET | `/` | Public (approved + available; paginated) |
| GET | `<id>/` | Public |
| POST | `create/` | Owner |
| GET | `my-cars/` | Owner |
| PATCH/DELETE | `<id>/manage/` | Owner |
| POST | `<id>/images/` | Owner |
| DELETE | `images/<id>/delete/` | Owner |
| GET | `admin/all/` | Admin |
| PATCH | `admin/<id>/approve/` | Admin |

Query params (public list): `search`, `car_type`, `min_price`, `max_price`, `ordering`, `page`.

### Bookings (`/api/bookings/`)

| Method | Endpoint | Access |
|--------|----------|--------|
| POST | `create/` | Customer |
| GET | `my-bookings/` | Customer |
| GET | `<id>/` | Customer / owner / admin |
| PATCH | `<id>/cancel/` | Customer |
| GET | `owner/` | Owner |
| PATCH | `<id>/manage/` | Owner (approve/reject) |
| PATCH | `<id>/complete/` | Owner |
| POST | `review/` | Customer |
| GET | `admin/all/` | Admin |
| PATCH | `admin/<id>/action/` | Admin |

---

## Project structure

```
rent_a_car/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
└── rentacar/                    # Django project root
    ├── manage.py
    ├── accounts/                # Users, profiles, auth API
    ├── cars/                    # Listings, images, public catalog
    ├── bookings/                # Bookings, reviews
    ├── rentacar/
    │   ├── settings.py
    │   ├── caching.py           # Redis + invalidation
    │   └── urls.py
    ├── static/
    │   ├── css/style.css
    │   └── js/api.js, ui.js
    ├── templates/
    │   ├── base.html
    │   ├── home.html
    │   ├── cars/
    │   ├── accounts/
    │   └── dashboards/
    └── media/                   # Uploaded images (runtime)
```

---

## Development notes

### Git / contribution

- Prefer feature branches and PRs into the main upstream repo.
- Do not commit secrets; use environment variables for `SECRET_KEY` and DB credentials in production.

### Manual smoke test

1. Register **owner** → create car → confirm it appears on **Browse** immediately.
2. Register **customer** → book car → owner **approves** → owner **completes** → customer **reviews**.
3. **Admin** → hide car → confirm it disappears from browse → restore.
4. Toggle **dark mode** on home and dashboards.
5. With 13+ cars, confirm **pagination** on Home/Browse.

### Troubleshooting

| Issue | Check |
|-------|--------|
| Browse shows 0 cars | Car must be `is_approved` and `is_available`; hard-refresh browser; `GET /api/cars/` should not be cached stale. |
| Port in use | Change `8002:8000` in `docker-compose.yml` or stop conflicting process. |
| Static files old | Run `collectstatic` and hard-refresh. |

---

## License

Specify your license here (e.g. MIT) if open-sourcing the project.
