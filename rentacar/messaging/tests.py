from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from bookings.models import Booking
from bookings.pricing import RENTAL_DAILY, day_end, day_start, normalize_booking_window
from cars.models import Car
from messaging.models import BookingMessage, BookingThreadRead

User = get_user_model()


def _auth(client, user):
    client.credentials(HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=user).key)


def _daily_window(start_d, end_d):
    start_at = day_start(timezone.make_aware(datetime.combine(start_d, time(9, 0))))
    end_at = day_end(timezone.make_aware(datetime.combine(end_d, time(17, 0))))
    return normalize_booking_window(RENTAL_DAILY, start_at, end_at)


class MessagingSetupMixin:
    def setUp(self):
        self.customer = User.objects.create_user(
            username='msgcust',
            email='msgcust@example.com',
            password='pass',
            role=User.Role.CUSTOMER,
        )
        self.owner = User.objects.create_user(
            username='msgowner',
            email='msgowner@example.com',
            password='pass',
            role=User.Role.OWNER,
        )
        self.admin = User.objects.create_user(
            username='msgadmin',
            email='msgadmin@example.com',
            password='pass',
            role=User.Role.ADMIN,
        )
        self.other = User.objects.create_user(
            username='msgother',
            email='msgother@example.com',
            password='pass',
            role=User.Role.CUSTOMER,
        )
        self.car = Car.objects.create(
            owner=self.owner,
            brand='Toyota',
            model='Corolla',
            year=2022,
            car_type='sedan',
            location='Lahore',
            rent_daily=True,
            price_per_day=50,
            is_available=True,
            is_approved=True,
        )
        start = timezone.localdate() + timedelta(days=5)
        end = start + timedelta(days=2)
        norm_start, norm_end = _daily_window(start, end)
        self.booking = Booking.objects.create(
            customer=self.customer,
            car=self.car,
            rental_type=RENTAL_DAILY,
            start_at=norm_start,
            end_at=norm_end,
            total_cost=Decimal('100.00'),
            status='pending',
            note='Need early pickup',
        )
        BookingMessage.objects.create(
            booking=self.booking,
            sender=self.customer,
            message_type=BookingMessage.MessageType.TEXT,
            body='Need early pickup',
        )


class MessagingThreadListTests(MessagingSetupMixin, APITestCase):
    def test_customer_sees_own_thread(self):
        _auth(self.client, self.customer)
        url = reverse('messaging-threads')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['booking_id'], self.booking.id)
        self.assertEqual(response.data['data'][0]['other_party_name'], 'Msgowner')

    def test_owner_sees_thread(self):
        _auth(self.client, self.owner)
        response = self.client.get(reverse('messaging-threads'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

    def test_admin_sees_all_threads(self):
        _auth(self.client, self.admin)
        response = self.client.get(reverse('messaging-threads'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)


class MessagingMessagesTests(MessagingSetupMixin, APITestCase):
    def test_owner_can_reply(self):
        _auth(self.client, self.owner)
        url = reverse('messaging-thread-messages', kwargs={'booking_id': self.booking.pk})
        response = self.client.post(url, {'body': 'Sure, 8am works.'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['body'], 'Sure, 8am works.')

    def test_outsider_forbidden(self):
        _auth(self.client, self.other)
        url = reverse('messaging-thread-messages', kwargs={'booking_id': self.booking.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_messages_marks_read(self):
        BookingMessage.objects.create(
            booking=self.booking,
            sender=self.owner,
            message_type=BookingMessage.MessageType.TEXT,
            body='Reply from owner',
        )
        _auth(self.client, self.customer)
        url = reverse('messaging-thread-messages', kwargs={'booking_id': self.booking.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['messages']), 2)
        self.assertTrue(BookingThreadRead.objects.filter(booking=self.booking, user=self.customer).exists())
        unread = self.client.get(reverse('messaging-unread-count'))
        self.assertEqual(unread.data['data']['count'], 0)

    def test_closed_booking_rejects_post(self):
        self.booking.status = 'completed'
        self.booking.save()
        _auth(self.client, self.customer)
        url = reverse('messaging-thread-messages', kwargs={'booking_id': self.booking.pk})
        response = self.client.post(url, {'body': 'Hello'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_post(self):
        _auth(self.client, self.admin)
        url = reverse('messaging-thread-messages', kwargs={'booking_id': self.booking.pk})
        response = self.client.post(url, {'body': 'Admin checking in.'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_customer_can_send_location(self):
        _auth(self.client, self.customer)
        url = reverse('messaging-thread-messages', kwargs={'booking_id': self.booking.pk})
        response = self.client.post(url, {
            'message_type': 'location',
            'latitude': '31.549700',
            'longitude': '74.343600',
            'label': 'Gulberg, Lahore',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data['data']
        self.assertEqual(data['message_type'], 'location')
        self.assertEqual(data['body'], 'Gulberg, Lahore')
        self.assertEqual(data['metadata']['latitude'], 31.5497)
        self.assertEqual(data['metadata']['longitude'], 74.3436)
        self.assertIn('maps?q=31.5497', data['maps_url'])

    def test_location_requires_coordinates(self):
        _auth(self.client, self.customer)
        url = reverse('messaging-thread-messages', kwargs={'booking_id': self.booking.pk})
        response = self.client.post(url, {'message_type': 'location'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_location_accepts_high_precision_coordinates(self):
        _auth(self.client, self.customer)
        url = reverse('messaging-thread-messages', kwargs={'booking_id': self.booking.pk})
        response = self.client.post(url, {
            'message_type': 'location',
            'latitude': 31.52043123456789,
            'longitude': 74.35872987654321,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data['data']
        self.assertEqual(data['metadata']['latitude'], 31.520431)
        self.assertEqual(data['metadata']['longitude'], 74.35873)

    def test_thread_preview_shows_location(self):
        BookingMessage.objects.create(
            booking=self.booking,
            sender=self.customer,
            message_type=BookingMessage.MessageType.LOCATION,
            body='Pickup spot',
            metadata={'latitude': 31.5, 'longitude': 74.3, 'label': 'Pickup spot'},
        )
        _auth(self.client, self.owner)
        response = self.client.get(reverse('messaging-threads'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        preview = response.data['data'][0]['last_message']
        self.assertIn('📍', preview)
        self.assertIn('Pickup spot', preview)

    def test_thread_messages_include_context_and_map_preview(self):
        _auth(self.client, self.customer)
        url = reverse('messaging-thread-messages', kwargs={'booking_id': self.booking.pk})
        response = self.client.post(url, {
            'message_type': 'location',
            'latitude': 31.520431,
            'longitude': 74.358730,
            'label': 'Gulberg',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('map_preview_url', response.data['data'])
        self.assertIn('/api/messaging/map-preview/', response.data['data']['map_preview_url'])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ctx = response.data['data']['context']
        self.assertEqual(ctx['booking_id'], self.booking.id)
        self.assertEqual(ctx['car_label'], 'Toyota Corolla (2022)')
        self.assertEqual(ctx['car_location'], 'Lahore')
        self.assertIn('other_party_name', ctx)


class MapPreviewTests(MessagingSetupMixin, APITestCase):
    def test_map_preview_returns_png(self):
        _auth(self.client, self.customer)
        url = reverse('messaging-map-preview')
        response = self.client.get(url, {'lat': '31.520431', 'lng': '74.358730'})
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_502_BAD_GATEWAY))
        if response.status_code == status.HTTP_200_OK:
            self.assertEqual(response['Content-Type'], 'image/png')
            self.assertTrue(len(response.content) > 100)

    def test_map_preview_rejects_invalid_coords(self):
        url = reverse('messaging-map-preview')
        response = self.client.get(url, {'lat': '999', 'lng': '74'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MessagingUnreadTests(MessagingSetupMixin, APITestCase):
    def test_unread_count_for_owner(self):
        _auth(self.client, self.owner)
        response = self.client.get(reverse('messaging-unread-count'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)


class BookingCreateMessagingHookTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username='bookcust',
            email='bookcust@example.com',
            password='pass',
            role=User.Role.CUSTOMER,
        )
        self.owner = User.objects.create_user(
            username='bookowner',
            email='bookowner@example.com',
            password='pass',
            role=User.Role.OWNER,
        )
        self.car = Car.objects.create(
            owner=self.owner,
            brand='Honda',
            model='Civic',
            year=2021,
            car_type='sedan',
            location='Karachi',
            rent_daily=True,
            price_per_day=60,
            is_available=True,
            is_approved=True,
        )
        _auth(self.client, self.customer)

    def test_booking_create_creates_messages_from_note(self):
        start = timezone.localdate() + timedelta(days=10)
        end = start + timedelta(days=1)
        norm_start, norm_end = _daily_window(start, end)
        url = reverse('booking-create')
        response = self.client.post(url, {
            'car': self.car.pk,
            'rental_type': RENTAL_DAILY,
            'start_at': norm_start.isoformat(),
            'end_at': norm_end.isoformat(),
            'note': 'Please include child seat',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        booking_id = response.data['booking']['id']
        messages = BookingMessage.objects.filter(booking_id=booking_id)
        self.assertGreaterEqual(messages.count(), 2)
        bodies = list(messages.values_list('body', flat=True))
        self.assertTrue(any('child seat' in b for b in bodies))
        self.assertTrue(any('submitted' in b.lower() for b in bodies))
