from django.contrib.auth import get_user_model

from .models import OwnerProfile
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

User = get_user_model()


class RegistrationSecurityTests(APITestCase):
    def test_register_rejects_admin_role(self):
        url = reverse('register')
        payload = {
            'username': 'eviladmin',
            'email': 'evil@example.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'role': 'admin',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='eviladmin').exists())

    def test_register_requires_password_match(self):
        url = reverse('register')
        payload = {
            'username': 'user1',
            'email': 'user1@example.com',
            'password': 'SecurePass123!',
            'password2': 'DifferentPass123!',
            'role': 'customer',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_customer_creates_profile(self):
        url = reverse('register')
        payload = {
            'username': 'cust1',
            'email': 'cust1@example.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'role': 'customer',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='cust1')
        self.assertEqual(user.role, User.Role.CUSTOMER)
        self.assertTrue(hasattr(user, 'customer_profile'))


class AuthThrottleTests(APITestCase):
    def test_login_endpoint_accessible(self):
        User.objects.create_user(
            username='loginuser',
            email='login@example.com',
            password='SecurePass123!',
            role=User.Role.CUSTOMER,
        )
        url = reverse('login')
        response = self.client.post(url, {
            'username': 'loginuser',
            'password': 'SecurePass123!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)


class DashboardOwnerListFilterTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='owneradmin',
            email='owneradmin@example.com',
            password='pass',
            role=User.Role.ADMIN,
        )
        verified_user = User.objects.create_user(
            username='verifiedowner',
            email='verified@example.com',
            password='pass',
            role=User.Role.OWNER,
        )
        pending_user = User.objects.create_user(
            username='pendingowner',
            email='pending@example.com',
            password='pass',
            role=User.Role.OWNER,
        )
        OwnerProfile.objects.create(user=verified_user, is_verified=True, phone_number='03001234567')
        OwnerProfile.objects.create(user=pending_user, is_verified=False, phone_number='03007654321')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=self.admin).key
        )
        self.url = reverse('admin-owner-list')

    def test_search_by_username(self):
        response = self.client.get(self.url, {'search': 'verified'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = {item['user']['username'] for item in response.data['results']}
        self.assertEqual(usernames, {'verifiedowner'})

    def test_filter_pending_verification(self):
        response = self.client.get(self.url, {'is_verified': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['user']['username'], 'pendingowner')

    def test_ordering_username(self):
        response = self.client.get(self.url, {'ordering': 'user__username'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item['user']['username'] for item in response.data['results']]
        self.assertEqual(names, sorted(names))

    def test_forbidden_for_customer(self):
        customer = User.objects.create_user(
            username='custownerlist',
            email='custownerlist@example.com',
            password='pass',
            role=User.Role.CUSTOMER,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=customer).key
        )
        response = self.client.get(self.url, {'search': 'verified'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
