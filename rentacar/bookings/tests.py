from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import OwnerProfile
from cars.models import Car
from .models import Booking

User = get_user_model()


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
            price_per_day=60,
            is_available=True,
            is_approved=True,
        )
        self.start = date.today() + timedelta(days=5)
        self.end = self.start + timedelta(days=3)
        Booking.objects.create(
            customer=self.customer,
            car=self.car,
            start_date=self.start,
            end_date=self.end,
            total_cost=180,
            status='approved',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=self.customer).key
        )

    def test_overlapping_booking_rejected(self):
        url = reverse('booking-create')
        overlap_start = self.start + timedelta(days=1)
        overlap_end = overlap_start + timedelta(days=2)
        response = self.client.post(url, {
            'car': self.car.pk,
            'start_date': overlap_start.isoformat(),
            'end_date': overlap_end.isoformat(),
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


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
            price_per_day=100,
            is_available=True,
            is_approved=True,
        )
        start = date.today() + timedelta(days=10)
        end = start + timedelta(days=2)
        self.booking = Booking.objects.create(
            customer=self.customer,
            car=self.car,
            start_date=start,
            end_date=end,
            total_cost=200,
            status='approved',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=self.owner).key
        )

    def test_complete_adds_earnings_once(self):
        url = reverse('booking-complete', kwargs={'pk': self.booking.pk})
        response = self.client.patch(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(float(self.profile.total_earnings), 200.0)

        response2 = self.client.patch(url, {}, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.profile.refresh_from_db()
        self.assertEqual(float(self.profile.total_earnings), 200.0)
