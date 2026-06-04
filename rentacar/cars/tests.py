from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Car

User = get_user_model()


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
