from django.contrib.auth import get_user_model

from .models import OwnerProfile, SocialMediaLink
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


class SocialMediaLinkAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='socialadmin',
            email='socialadmin@example.com',
            password='pass',
            role=User.Role.ADMIN,
        )
        self.customer = User.objects.create_user(
            username='socialcust',
            email='socialcust@example.com',
            password='pass',
            role=User.Role.CUSTOMER,
        )
        self.active = SocialMediaLink.objects.create(
            platform_name='Facebook',
            url='https://facebook.com/rentacar',
            is_active=True,
        )
        self.inactive = SocialMediaLink.objects.create(
            platform_name='Instagram',
            url='https://instagram.com/rentacar',
            is_active=False,
        )
        self.public_url = reverse('social-media-list')
        self.admin_list_url = reverse('admin-social-media-list')

    def test_public_list_returns_only_active_links(self):
        response = self.client.get(self.public_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['platform_name'], 'Facebook')

    def test_admin_can_create_update_and_delete(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=self.admin).key
        )
        create_response = self.client.post(self.admin_list_url, {
            'platform_name': 'LinkedIn',
            'url': 'https://linkedin.com/company/rentacar',
            'is_active': True,
        }, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        link_id = create_response.data['id']

        detail_url = reverse('admin-social-media-detail', kwargs={'pk': link_id})
        patch_response = self.client.patch(detail_url, {'is_active': False}, format='json')
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertFalse(patch_response.data['is_active'])

        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SocialMediaLink.objects.filter(pk=link_id).exists())

    def test_non_admin_cannot_manage_social_links(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=self.customer).key
        )
        response = self.client.get(self.admin_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
