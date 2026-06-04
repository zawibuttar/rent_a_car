from django.contrib.auth import get_user_model
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
