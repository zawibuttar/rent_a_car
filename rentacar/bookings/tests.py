from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import OwnerProfile
from cars.models import Car
from .models import Booking
from .pricing import (
    RENTAL_DAILY,
    RENTAL_HOURLY,
    RENTAL_MONTHLY,
    RENTAL_TYPE_CHOICES,
    RENTAL_WEEKLY,
    compute_total,
    day_end,
    day_start,
    normalize_booking_window,
)
from .enums import RentalDuration

User = get_user_model()


def _auth(client, user):
    client.credentials(
        HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=user).key
    )


def _daily_window(start_d, end_d):
    start_at = day_start(timezone.make_aware(datetime.combine(start_d, time(9, 0))))
    end_at = day_end(timezone.make_aware(datetime.combine(end_d, time(17, 0))))
    return normalize_booking_window(RENTAL_DAILY, start_at, end_at)


def _booking_payload(car_id, rental_type, start_at, end_at, note=''):
    return {
        'car': car_id,
        'rental_type': rental_type,
        'start_at': start_at.isoformat(),
        'end_at': end_at.isoformat(),
        'note': note,
    }


class BookingOverlapTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='ownerb',
            email='ownerb@example.com',
            password='pass',
            role=User.Role.OWNER,
        )
        OwnerProfile.objects.create(user=self.owner)
        self.customer = User.objects.create_user(
            username='custb',
            email='custb@example.com',
            password='pass',
            role=User.Role.CUSTOMER,
        )
        self.car = Car.objects.create(
            owner=self.owner,
            brand='Ford',
            model='Focus',
            year=2020,
            car_type='sedan',
            description='Rental',
            location='Chicago',
            rent_daily=True,
            price_per_day=60,
            is_available=True,
            is_approved=True,
        )
        self.start = date.today() + timedelta(days=5)
        self.end = self.start + timedelta(days=3)
        norm_start, norm_end = _daily_window(self.start, self.end)
        Booking.objects.create(
            customer=self.customer,
            car=self.car,
            rental_type=RENTAL_DAILY,
            start_at=norm_start,
            end_at=norm_end,
            total_cost=compute_total(self.car, RENTAL_DAILY, norm_start, norm_end),
            status='approved',
        )
        _auth(self.client, self.customer)

    def test_overlapping_booking_rejected(self):
        url = reverse('booking-create')
        overlap_start = self.start + timedelta(days=1)
        overlap_end = overlap_start + timedelta(days=2)
        start_at = day_start(
            timezone.make_aware(datetime.combine(overlap_start, time.min))
        )
        end_at = day_end(
            timezone.make_aware(datetime.combine(overlap_end, time(23, 59, 59)))
        )
        response = self.client.post(
            url,
            _booking_payload(self.car.pk, RENTAL_DAILY, start_at, end_at),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class BookingRentalTypeTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='ownerr',
            email='ownerr@example.com',
            password='pass',
            role=User.Role.OWNER,
        )
        OwnerProfile.objects.create(user=self.owner)
        self.customer = User.objects.create_user(
            username='custr',
            email='custr@example.com',
            password='pass',
            role=User.Role.CUSTOMER,
        )
        self.car = Car.objects.create(
            owner=self.owner,
            brand='Multi',
            model='Rental',
            year=2021,
            car_type='sedan',
            description='',
            location='Austin',
            rent_hourly=True,
            rent_daily=True,
            rent_weekly=True,
            rent_monthly=True,
            price_per_hour=Decimal('15.00'),
            price_per_day=Decimal('80.00'),
            price_per_week=Decimal('400.00'),
            price_per_month=Decimal('1500.00'),
            is_available=True,
            is_approved=True,
        )
        _auth(self.client, self.customer)
        self.create_url = reverse('booking-create')

    def test_same_day_daily_accepted(self):
        d = date.today() + timedelta(days=3)
        start_at = day_start(timezone.make_aware(datetime.combine(d, time.min)))
        end_at = day_end(timezone.make_aware(datetime.combine(d, time(12, 0))))
        response = self.client.post(
            self.create_url,
            _booking_payload(self.car.pk, RENTAL_DAILY, start_at, end_at),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        booking_data = response.data['booking']
        booking = Booking.objects.get(pk=booking_data['id'])
        expected = compute_total(self.car, RENTAL_DAILY, start_at, end_at)
        self.assertEqual(booking.total_cost, expected)
        self.assertEqual(float(booking_data['total_cost']), 80.0)

    def test_hourly_under_one_hour_rejected(self):
        start = timezone.now() + timedelta(hours=2)
        end = start + timedelta(minutes=30)
        response = self.client.post(
            self.create_url,
            _booking_payload(self.car.pk, RENTAL_HOURLY, start, end),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_hourly_prorated_cost(self):
        start = timezone.now() + timedelta(hours=2)
        end = start + timedelta(hours=1, minutes=20)
        expected = float(compute_total(self.car, RENTAL_HOURLY, start, end))
        response = self.client.post(
            self.create_url,
            _booking_payload(self.car.pk, RENTAL_HOURLY, start, end),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['booking']['total_cost']), expected)
        self.assertEqual(expected, 20.0)

    def test_weekly_without_seven_days_rejected(self):
        start_d = date.today() + timedelta(days=10)
        end_d = start_d + timedelta(days=5)
        start_at = day_start(timezone.make_aware(datetime.combine(start_d, time.min)))
        end_at = day_end(
            timezone.make_aware(datetime.combine(end_d, time(23, 59, 59)))
        )
        response = self.client.post(
            self.create_url,
            _booking_payload(self.car.pk, RENTAL_WEEKLY, start_at, end_at),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recomputes_total_not_client_value(self):
        d = date.today() + timedelta(days=20)
        start_at = day_start(timezone.make_aware(datetime.combine(d, time.min)))
        end_at = day_end(
            timezone.make_aware(datetime.combine(d, time(23, 59, 59)))
        )
        payload = _booking_payload(self.car.pk, RENTAL_DAILY, start_at, end_at)
        response = self.client.post(self.create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['booking']['total_cost']), 80.0)


class CompleteBookingEarningsTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='ownere',
            email='ownere@example.com',
            password='pass',
            role=User.Role.OWNER,
        )
        self.profile = OwnerProfile.objects.create(user=self.owner, total_earnings=0)
        self.customer = User.objects.create_user(
            username='custe',
            email='custe@example.com',
            password='pass',
            role=User.Role.CUSTOMER,
        )
        self.car = Car.objects.create(
            owner=self.owner,
            brand='Mazda',
            model='3',
            year=2022,
            car_type='sedan',
            description='',
            location='Miami',
            rent_daily=True,
            price_per_day=100,
            is_available=True,
            is_approved=True,
        )
        start = date.today() + timedelta(days=10)
        end = start + timedelta(days=2)
        norm_start, norm_end = _daily_window(start, end)
        self.booking = Booking.objects.create(
            customer=self.customer,
            car=self.car,
            rental_type=RENTAL_DAILY,
            start_at=norm_start,
            end_at=norm_end,
            total_cost=compute_total(self.car, RENTAL_DAILY, norm_start, norm_end),
            status='approved',
        )
        _auth(self.client, self.owner)

    def test_complete_adds_earnings_once(self):
        url = reverse('booking-complete', kwargs={'pk': self.booking.pk})
        response = self.client.patch(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(float(self.profile.total_earnings), float(self.booking.total_cost))

        response2 = self.client.patch(url, {}, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.profile.refresh_from_db()
        self.assertEqual(float(self.profile.total_earnings), float(self.booking.total_cost))


class PricingComputeTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='ownerp',
            email='ownerp@example.com',
            password='pass',
            role=User.Role.OWNER,
        )
        self.car = Car.objects.create(
            owner=self.owner,
            brand='Test',
            model='Car',
            year=2020,
            car_type='sedan',
            description='',
            location='NYC',
            rent_hourly=True,
            rent_daily=True,
            rent_weekly=True,
            rent_monthly=True,
            price_per_hour=Decimal('10'),
            price_per_day=Decimal('50'),
            price_per_week=Decimal('300'),
            price_per_month=Decimal('1200'),
            is_available=True,
            is_approved=True,
        )

    def test_monthly_minimum_thirty_days(self):
        start_d = date.today() + timedelta(days=40)
        end_d = start_d + timedelta(days=28)
        start_at = day_start(timezone.make_aware(datetime.combine(start_d, time.min)))
        end_at = day_end(
            timezone.make_aware(datetime.combine(end_d, time(23, 59, 59)))
        )
        with self.assertRaises(ValueError):
            compute_total(self.car, RENTAL_MONTHLY, start_at, end_at)


class DashboardBookingListFilterTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='bookadmin',
            email='bookadmin@example.com',
            password='pass',
            role=User.Role.ADMIN,
        )
        self.owner = User.objects.create_user(
            username='bookowner',
            email='bookowner@example.com',
            password='pass',
            role=User.Role.OWNER,
        )
        OwnerProfile.objects.create(user=self.owner)
        self.customer = User.objects.create_user(
            username='johnbook',
            email='john@example.com',
            password='pass',
            role=User.Role.CUSTOMER,
        )
        self.other_customer = User.objects.create_user(
            username='affanbook',
            email='affan@example.com',
            password='pass',
            role=User.Role.CUSTOMER,
        )
        self.toyota = Car.objects.create(
            owner=self.owner,
            brand='Toyota',
            model='Corolla',
            year=2022,
            car_type='sedan',
            description='',
            location='Lahore',
            rent_daily=True,
            price_per_day=50,
            is_available=True,
            is_approved=True,
        )
        self.honda = Car.objects.create(
            owner=self.owner,
            brand='Honda',
            model='Civic',
            year=2021,
            car_type='sedan',
            description='',
            location='Karachi',
            rent_daily=True,
            price_per_day=60,
            is_available=True,
            is_approved=True,
        )
        start = date.today() + timedelta(days=10)
        norm_start, norm_end = _daily_window(start, start)
        Booking.objects.create(
            customer=self.customer,
            car=self.toyota,
            rental_type=RENTAL_DAILY,
            start_at=norm_start,
            end_at=norm_end,
            total_cost=Decimal('50'),
            status='pending',
        )
        norm_start2, norm_end2 = _daily_window(start + timedelta(days=1), start + timedelta(days=1))
        Booking.objects.create(
            customer=self.other_customer,
            car=self.honda,
            rental_type=RENTAL_DAILY,
            start_at=norm_start2,
            end_at=norm_end2,
            total_cost=Decimal('80'),
            status='approved',
        )
        self.admin_url = reverse('admin-booking-list')
        self.my_url = reverse('my-bookings')
        self.owner_url = reverse('owner-bookings')

    def test_admin_search_customer(self):
        _auth(self.client, self.admin)
        response = self.client.get(self.admin_url, {'search': 'john'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['customer']['username'], 'johnbook')

    def test_admin_status_filter(self):
        _auth(self.client, self.admin)
        response = self.client.get(self.admin_url, {'status': 'approved'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(b['status'] == 'approved' for b in response.data['results']))

    def test_admin_ordering_total_cost(self):
        _auth(self.client, self.admin)
        response = self.client.get(self.admin_url, {'ordering': '-total_cost'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        costs = [float(b['total_cost']) for b in response.data['results']]
        self.assertEqual(costs, sorted(costs, reverse=True))

    def test_my_bookings_search_car(self):
        _auth(self.client, self.customer)
        response = self.client.get(self.my_url, {'search': 'toyota'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_owner_bookings_search_customer(self):
        _auth(self.client, self.owner)
        response = self.client.get(self.owner_url, {'search': 'affan', 'status': 'approved'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class RentalDurationEnumTests(APITestCase):
    def test_rental_duration_matches_pricing_constants(self):
        self.assertEqual(RENTAL_HOURLY, RentalDuration.HOURLY)
        self.assertEqual(RENTAL_DAILY, RentalDuration.DAILY)
        self.assertEqual(RENTAL_WEEKLY, RentalDuration.WEEKLY)
        self.assertEqual(RENTAL_MONTHLY, RentalDuration.MONTHLY)
        self.assertEqual(RENTAL_TYPE_CHOICES, RentalDuration.choices)


class RentalDurationEnumTests(APITestCase):
    def test_rental_duration_matches_pricing_constants(self):
        self.assertEqual(RENTAL_HOURLY, RentalDuration.HOURLY)
        self.assertEqual(RENTAL_DAILY, RentalDuration.DAILY)
        self.assertEqual(RENTAL_WEEKLY, RentalDuration.WEEKLY)
        self.assertEqual(RENTAL_MONTHLY, RentalDuration.MONTHLY)
        self.assertEqual(RENTAL_TYPE_CHOICES, RentalDuration.choices)
