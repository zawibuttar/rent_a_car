from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import OwnerProfile
from bookings.models import Booking, Review
from bookings.pricing import RENTAL_DAILY, day_end, day_start, normalize_booking_window
from rentacar.utils import format_display_name
from .geocoding import search_cities
from .models import Car


def _daily_window(start_d, end_d):
    start_at = day_start(timezone.make_aware(datetime.combine(start_d, time(9, 0))))
    end_at = day_end(timezone.make_aware(datetime.combine(end_d, time(17, 0))))
    return normalize_booking_window(RENTAL_DAILY, start_at, end_at)

User = get_user_model()


class DisplayNameTests(APITestCase):
    def test_format_display_name_capitalizes_username(self):
        self.assertEqual(format_display_name('ahmad'), 'Ahmad')
        self.assertEqual(format_display_name('ahmed'), 'Ahmed')
        self.assertEqual(format_display_name('ahmed_ali'), 'Ahmed Ali')


class PublicCarListTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner1',
            email='owner1@example.com',
            password='pass',
            role=User.Role.OWNER,
        )
        Car.objects.create(
            owner=self.owner,
            brand='Toyota',
            model='Camry',
            year=2020,
            car_type='sedan',
            description='Visible car',
            location='NYC',
            price_per_day=50,
            is_available=True,
            is_approved=True,
        )
        Car.objects.create(
            owner=self.owner,
            brand='Honda',
            model='Civic',
            year=2021,
            car_type='sedan',
            description='Los Angeles car',
            location='Los Angeles, CA',
            price_per_day=55,
            is_available=True,
            is_approved=True,
        )
        Car.objects.create(
            owner=self.owner,
            brand='Hidden',
            model='Car',
            year=2019,
            car_type='sedan',
            description='Not approved',
            location='LA',
            price_per_day=40,
            is_available=True,
            is_approved=False,
        )

    def test_public_list_only_approved_available(self):
        url = reverse('car-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        brands = [c['brand'] for c in response.data['results']]
        self.assertIn('Toyota', brands)
        self.assertNotIn('Hidden', brands)

    def test_public_list_filters_by_location(self):
        url = reverse('car-list')
        response = self.client.get(url, {'location': 'NYC'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        brands = [c['brand'] for c in response.data['results']]
        self.assertEqual(brands, ['Toyota'])
        self.assertNotIn('Honda', brands)
        self.assertNotIn('Hidden', brands)

    def test_public_list_filters_by_city_alias(self):
        url = reverse('car-list')
        response = self.client.get(url, {'city': 'Los Angeles'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        brands = [c['brand'] for c in response.data['results']]
        self.assertEqual(brands, ['Honda'])
        self.assertNotIn('Toyota', brands)


class CarReviewsDisplayTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='ownerr',
            email='ownerr@example.com',
            password='pass',
            role=User.Role.OWNER,
        )
        self.customer = User.objects.create_user(
            username='custr',
            email='custr@example.com',
            password='pass',
            role=User.Role.CUSTOMER,
        )
        self.car = Car.objects.create(
            owner=self.owner,
            brand='Reviewed',
            model='Car',
            year=2022,
            car_type='sedan',
            description='',
            location='Lahore',
            price_per_day=40,
            is_available=True,
            is_approved=True,
        )
        start = timezone.now() - timedelta(days=10)
        end = start + timedelta(days=2)
        booking = Booking.objects.create(
            customer=self.customer,
            car=self.car,
            rental_type='daily',
            start_at=start,
            end_at=end,
            total_cost=Decimal('80.00'),
            status='completed',
        )
        Review.objects.create(
            booking=booking,
            reviewer=self.customer,
            rating=5,
            comment='Great car, smooth ride.',
        )

    def test_list_includes_review_stats(self):
        url = reverse('car-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = next(c for c in response.data['results'] if c['brand'] == 'Reviewed')
        self.assertEqual(row['review_count'], 1)
        self.assertEqual(float(row['average_rating']), 5.0)

    def test_detail_includes_reviews(self):
        url = reverse('car-detail', kwargs={'pk': self.car.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['review_summary']['count'], 1)
        self.assertEqual(response.data['review_summary']['average_rating'], 5.0)
        self.assertEqual(len(response.data['reviews']), 1)
        self.assertEqual(response.data['reviews'][0]['comment'], 'Great car, smooth ride.')


class BookedSlotsDisplayTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner_slots',
            email='owner_slots@example.com',
            password='pass',
            role=User.Role.OWNER,
        )
        self.customer = User.objects.create_user(
            username='cust_slots',
            email='cust_slots@example.com',
            password='pass',
            role=User.Role.CUSTOMER,
        )
        self.car = Car.objects.create(
            owner=self.owner,
            brand='Slot',
            model='Test',
            year=2021,
            car_type='sedan',
            description='',
            location='Austin',
            rent_daily=True,
            price_per_day=50,
            is_available=True,
            is_approved=True,
        )

    def test_future_approved_booking_in_list_slots(self):
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=2)
        norm_start, norm_end = _daily_window(start, end)
        Booking.objects.create(
            customer=self.customer,
            car=self.car,
            rental_type='daily',
            start_at=norm_start,
            end_at=norm_end,
            total_cost=Decimal('150.00'),
            status='approved',
        )
        url = reverse('car-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = next(c for c in response.data['results'] if c['brand'] == 'Slot')
        self.assertEqual(row['booked_slots_total'], 1)
        self.assertEqual(len(row['booked_slots']), 1)
        self.assertEqual(row['booked_slots'][0]['status'], 'approved')
        self.assertEqual(row['booked_slots'][0]['start_at'], norm_start.isoformat())
        self.assertFalse(row['is_currently_booked'])

    def test_completed_booking_excluded(self):
        past_start = timezone.now() - timedelta(days=5)
        past_end = past_start + timedelta(days=2)
        Booking.objects.create(
            customer=self.customer,
            car=self.car,
            rental_type='daily',
            start_at=past_start,
            end_at=past_end,
            total_cost=Decimal('100.00'),
            status='completed',
        )
        url = reverse('car-detail', kwargs={'pk': self.car.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['booked_slots_total'], 0)
        self.assertEqual(response.data['booked_slots'], [])
        self.assertFalse(response.data['is_currently_booked'])

    def test_currently_active_booking(self):
        now = timezone.now()
        start = now - timedelta(hours=2)
        end = now + timedelta(days=1)
        norm_start, norm_end = _daily_window(
            timezone.localdate(start),
            timezone.localdate(end),
        )
        Booking.objects.create(
            customer=self.customer,
            car=self.car,
            rental_type='daily',
            start_at=norm_start,
            end_at=norm_end,
            total_cost=Decimal('50.00'),
            status='approved',
        )
        url = reverse('car-detail', kwargs={'pk': self.car.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_currently_booked'])
        self.assertTrue(response.data['booked_slots'][0]['is_active'])

    def test_list_prefetch_avoids_per_car_booking_queries(self):
        car_two = Car.objects.create(
            owner=self.owner,
            brand='Second',
            model='Car',
            year=2022,
            car_type='sedan',
            description='',
            location='Austin',
            rent_daily=True,
            price_per_day=45,
            is_available=True,
            is_approved=True,
        )
        for car in (self.car, car_two):
            start = date.today() + timedelta(days=12)
            end = start + timedelta(days=1)
            norm_start, norm_end = _daily_window(start, end)
            Booking.objects.create(
                customer=self.customer,
                car=car,
                rental_type='daily',
                start_at=norm_start,
                end_at=norm_end,
                total_cost=Decimal('50.00'),
                status='approved',
            )
        url = reverse('car-list')
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        booking_queries = [
            q for q in ctx.captured_queries
            if 'bookings_booking' in q['sql'].lower()
            and 'select' in q['sql'].lower()
        ]
        # One batched prefetch for active bookings; not one query per car (N+1).
        self.assertLessEqual(
            len(booking_queries),
            2,
            msg='Expected batched booking prefetch, got: '
            + '; '.join(q['sql'][:80] for q in booking_queries),
        )


class LocationSearchApiTests(APITestCase):
    @patch('cars.geocoding._fetch_json')
    def test_location_search_returns_normalized_cities(self, mock_fetch):
        mock_fetch.return_value = [{
            'lat': '31.5497',
            'lon': '74.3436',
            'display_name': 'Lahore, Punjab, Pakistan',
            'address': {'city': 'Lahore'},
        }]
        url = reverse('location-search')
        response = self.client.get(url, {'q': 'Lahore'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['label'], 'Lahore')

    def test_location_search_requires_min_length(self):
        url = reverse('location-search')
        response = self.client.get(url, {'q': 'L'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    @patch('cars.geocoding._fetch_json')
    def test_search_cities_uses_cache(self, mock_fetch):
        mock_fetch.return_value = [{
            'lat': '24.86',
            'lon': '67.00',
            'display_name': 'Karachi, Pakistan',
            'address': {'city': 'Karachi'},
        }]
        search_cities('Karachi')
        search_cities('Karachi')
        mock_fetch.assert_called_once()


@override_settings(CACHE_ENABLED=True)
class AdminCarListPaginationCacheTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_user(
            username='admincache',
            email='admincache@example.com',
            password='pass',
            role=User.Role.ADMIN,
        )
        self.owner = User.objects.create_user(
            username='ownercache',
            email='ownercache@example.com',
            password='pass',
            role=User.Role.OWNER,
        )
        for i in range(15):
            Car.objects.create(
                owner=self.owner,
                brand='Brand',
                model=f'Model{i}',
                year=2020 + (i % 5),
                car_type='sedan',
                description=f'Car {i}',
                location='Test City',
                price_per_day=40 + i,
                is_available=True,
                is_approved=True,
            )
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=self.admin).key
        )
        self.url = reverse('admin-car-list')

    def test_page_one_and_page_two_return_different_results(self):
        page1 = self.client.get(self.url, {'page': 1})
        page2 = self.client.get(self.url, {'page': 2})
        self.assertEqual(page1.status_code, status.HTTP_200_OK)
        self.assertEqual(page2.status_code, status.HTTP_200_OK)
        ids1 = {item['id'] for item in page1.data['results']}
        ids2 = {item['id'] for item in page2.data['results']}
        self.assertTrue(ids1)
        self.assertTrue(ids2)
        self.assertFalse(ids1 & ids2)

    def test_cached_pages_stay_distinct_after_repeat_requests(self):
        self.client.get(self.url, {'page': 1})
        self.client.get(self.url, {'page': 2})
        page2_again = self.client.get(self.url, {'page': 2})
        page1_again = self.client.get(self.url, {'page': 1})
        ids1 = {item['id'] for item in page1_again.data['results']}
        ids2 = {item['id'] for item in page2_again.data['results']}
        self.assertFalse(ids1 & ids2)


class AdminCarApprovalTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin1',
            email='admin1@example.com',
            password='pass',
            role=User.Role.ADMIN,
        )
        self.owner = User.objects.create_user(
            username='owner2',
            email='owner2@example.com',
            password='pass',
            role=User.Role.OWNER,
        )
        self.car = Car.objects.create(
            owner=self.owner,
            brand='Honda',
            model='Civic',
            year=2021,
            car_type='sedan',
            description='Test',
            location='Boston',
            price_per_day=45,
            is_available=True,
            is_approved=True,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=self.admin).key
        )

    def test_is_approved_string_false_coerced(self):
        url = reverse('admin-car-approve', kwargs={'pk': self.car.pk})
        response = self.client.patch(url, {'is_approved': 'false'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.car.refresh_from_db()
        self.assertFalse(self.car.is_approved)


class OwnerCarRentalOptionsTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner3',
            email='owner3@example.com',
            password='pass',
            role=User.Role.OWNER,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=self.owner).key
        )

    def test_create_listing_with_multiple_rental_prices(self):
        url = reverse('car-create')
        response = self.client.post(url, {
            'brand': 'BMW',
            'model': 'X3',
            'year': 2023,
            'car_type': 'suv',
            'description': 'Premium',
            'location': 'Seattle',
            'rent_hourly': True,
            'rent_daily': True,
            'rent_weekly': False,
            'rent_monthly': False,
            'price_per_hour': '25.00',
            'price_per_day': '120.00',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        car = Car.objects.get(pk=response.data['car']['id'])
        self.assertTrue(car.rent_hourly)
        self.assertTrue(car.rent_daily)
        self.assertEqual(float(car.price_per_hour), 25.0)
        self.assertEqual(float(car.price_per_day), 120.0)

    def test_create_requires_price_for_enabled_type(self):
        url = reverse('car-create')
        response = self.client.post(url, {
            'brand': 'No',
            'model': 'Price',
            'year': 2022,
            'car_type': 'sedan',
            'description': '',
            'location': 'Denver',
            'rent_hourly': True,
            'rent_daily': False,
            'rent_weekly': False,
            'rent_monthly': False,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DashboardCarListFilterTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='filteradmin',
            email='filteradmin@example.com',
            password='pass',
            role=User.Role.ADMIN,
        )
        self.owner = User.objects.create_user(
            username='toyotaowner',
            email='toyotaowner@example.com',
            password='pass',
            role=User.Role.OWNER,
        )
        OwnerProfile.objects.create(user=self.owner, is_verified=True)
        self.live_car = Car.objects.create(
            owner=self.owner,
            brand='Toyota',
            model='Corolla',
            year=2022,
            car_type='sedan',
            description='',
            location='Lahore',
            price_per_day=50,
            is_available=True,
            is_approved=True,
        )
        Car.objects.create(
            owner=self.owner,
            brand='Honda',
            model='Civic',
            year=2021,
            car_type='suv',
            description='',
            location='Karachi',
            price_per_day=80,
            is_available=False,
            is_approved=True,
        )
        Car.objects.create(
            owner=self.owner,
            brand='Suzuki',
            model='Alto',
            year=2020,
            car_type='hatchback',
            description='',
            location='Islamabad',
            price_per_day=30,
            is_available=True,
            is_approved=False,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=self.admin).key
        )
        self.admin_url = reverse('admin-car-list')
        self.owner_client = self.client.__class__()
        self.owner_client.credentials(
            HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=self.owner).key
        )
        self.my_cars_url = reverse('my-car')

    def test_admin_search_by_brand(self):
        response = self.client.get(self.admin_url, {'search': 'corolla'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        brands = {item['brand'] for item in response.data['results']}
        self.assertEqual(brands, {'Toyota'})

    def test_admin_listing_live_filter(self):
        response = self.client.get(self.admin_url, {'listing': 'live'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['brand'], 'Toyota')

    def test_admin_is_available_filter(self):
        response = self.client.get(self.admin_url, {'is_available': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertTrue(all(c['is_available'] for c in response.data['results']))

    def test_admin_ordering_price(self):
        response = self.client.get(self.admin_url, {'ordering': 'price_per_day'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = [float(c['price_per_day']) for c in response.data['results']]
        self.assertEqual(prices, sorted(prices))

    def test_my_cars_search_and_listing(self):
        response = self.owner_client.get(self.my_cars_url, {'search': 'honda', 'listing': 'paused'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['brand'], 'Honda')

    def test_admin_list_forbidden_for_customer(self):
        customer = User.objects.create_user(
            username='custfilter',
            email='custfilter@example.com',
            password='pass',
            role=User.Role.CUSTOMER,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=customer).key
        )
        response = self.client.get(self.admin_url, {'search': 'toyota'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class OwnerAdminRemovedCarTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='removedowner',
            email='removedowner@example.com',
            password='pass',
            role=User.Role.OWNER,
        )
        self.live_car = Car.objects.create(
            owner=self.owner,
            brand='Toyota',
            model='Yaris',
            year=2022,
            car_type='sedan',
            description='',
            location='Lahore',
            price_per_day=40,
            is_available=True,
            is_approved=True,
        )
        self.removed_car = Car.objects.create(
            owner=self.owner,
            brand='Suzuki',
            model='Alto',
            year=2020,
            car_type='hatchback',
            description='',
            location='Karachi',
            price_per_day=25,
            is_available=True,
            is_approved=False,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=self.owner).key
        )
        self.manage_url = reverse('car-manage', kwargs={'pk': self.removed_car.pk})
        self.live_manage_url = reverse('car-manage', kwargs={'pk': self.live_car.pk})

    def test_owner_cannot_update_admin_removed_listing(self):
        response = self.client.patch(
            self.manage_url,
            {'brand': 'Changed', 'price_per_day': '99.00'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.removed_car.refresh_from_db()
        self.assertEqual(self.removed_car.brand, 'Suzuki')

    def test_owner_can_delete_admin_removed_listing(self):
        response = self.client.delete(self.manage_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Car.objects.filter(pk=self.removed_car.pk).exists())

    def test_owner_can_still_update_live_listing(self):
        response = self.client.patch(
            self.live_manage_url,
            {'brand': 'Toyota Updated'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.live_car.refresh_from_db()
        self.assertEqual(self.live_car.brand, 'Toyota Updated')

    def test_owner_cannot_upload_images_to_admin_removed_listing(self):
        url = reverse('car-image-upload', kwargs={'pk': self.removed_car.pk})
        response = self.client.post(url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
