from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from announcements.models import Announcement, AnnouncementRead

User = get_user_model()


def _auth(client, user):
    client.credentials(HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=user).key)


class AnnouncementSetupMixin:
    def setUp(self):
        self.customer = User.objects.create_user(
            username='anncust',
            email='anncust@example.com',
            password='pass',
            role=User.Role.CUSTOMER,
        )
        self.owner = User.objects.create_user(
            username='annowner',
            email='annowner@example.com',
            password='pass',
            role=User.Role.OWNER,
        )
        self.admin = User.objects.create_user(
            username='annadmin',
            email='annadmin@example.com',
            password='pass',
            role=User.Role.ADMIN,
        )
        self.announcement = Announcement.objects.create(
            title='Holiday hours',
            body='Support is limited on Sunday.',
            audience=Announcement.Audience.ALL,
            created_by=self.admin,
        )


class AnnouncementUserTests(AnnouncementSetupMixin, APITestCase):
    def test_customer_sees_all_audience(self):
        _auth(self.client, self.customer)
        response = self.client.get(reverse('announcement-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

    def test_owner_does_not_see_customers_only(self):
        Announcement.objects.create(
            title='Customer promo',
            body='Customers only',
            audience=Announcement.Audience.CUSTOMERS,
            created_by=self.admin,
        )
        _auth(self.client, self.owner)
        response = self.client.get(reverse('announcement-list'))
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['title'], 'Holiday hours')

    def test_unread_count(self):
        _auth(self.client, self.customer)
        response = self.client.get(reverse('announcement-unread-count'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)

    def test_mark_read_reduces_unread(self):
        _auth(self.client, self.customer)
        url = reverse('announcement-read', kwargs={'pk': self.announcement.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        unread = self.client.get(reverse('announcement-unread-count'))
        self.assertEqual(unread.data['data']['count'], 0)

    def test_dismiss_banner(self):
        _auth(self.client, self.customer)
        url = reverse('announcement-dismiss-banner', kwargs={'pk': self.announcement.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        banner = self.client.get(reverse('announcement-banner'))
        self.assertIsNone(banner.data['data'])

    def test_expired_announcement_hidden(self):
        self.announcement.expires_at = timezone.now() - timedelta(hours=1)
        self.announcement.save()
        _auth(self.client, self.customer)
        response = self.client.get(reverse('announcement-list'))
        self.assertEqual(len(response.data['data']), 0)

    def test_admin_does_not_see_consumer_list(self):
        _auth(self.client, self.admin)
        response = self.client.get(reverse('announcement-list'))
        self.assertEqual(len(response.data['data']), 0)


class AnnouncementAdminTests(AnnouncementSetupMixin, APITestCase):
    def test_admin_can_create(self):
        _auth(self.client, self.admin)
        response = self.client.post(reverse('announcement-admin-list'), {
            'title': 'New policy',
            'body': 'Please review the updated terms.',
            'audience': 'owners',
            'is_active': True,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['title'], 'New policy')

    def test_customer_cannot_create(self):
        _auth(self.client, self.customer)
        response = self.client.post(reverse('announcement-admin-list'), {
            'title': 'Hack',
            'body': 'Nope',
            'audience': 'all',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_deactivate(self):
        _auth(self.client, self.admin)
        url = reverse('announcement-admin-detail', kwargs={'pk': self.announcement.pk})
        response = self.client.patch(url, {'is_active': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        _auth(self.client, self.customer)
        listed = self.client.get(reverse('announcement-list'))
        self.assertEqual(len(listed.data['data']), 0)
