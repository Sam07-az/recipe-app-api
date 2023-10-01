"""
Tests for the usesr API 
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')

def create_user(**params):
    """ create and return a new user"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """ test the public features of the user api"""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """test creating a user is successfull"""
        paylod = {
            'email':'test@example.com',
            'password':'testpass123',
            'name':'Test Name' 
        }
        res = self.client.post(CREATE_USER_URL,paylod)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=paylod['email'])
        self.assertTrue(user.check_password(paylod['password']))
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        """test error retured if user with email exists"""
        paylod = {
            'email':'test@example.com',
            'password':'testpass123',
            'name':'Test Name' 
        }
        create_user(**paylod)
        res = self.client.post(CREATE_USER_URL,paylod)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """ test an error is returned if password is less than 5 chars"""
        paylod = {
            'email':'test@example.com',
            'password':'pw',
            'name':'Test Name' 
        }
        res = self.client.post(CREATE_USER_URL,paylod)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=paylod['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """ test generates token for valid credentials"""
        user_details = {
            'email': 'test@example.com',
            'name': 'Test name',
            'password': 'test-user-password123'
        }
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password']
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test returns error if credentials invalid"""
        create_user(email='test@example.com', password='goodpass')

        payload = {'email':'test@example.com', 'password': 'badpass'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test posting a blank password return a error"""
        payload = {'email':'test@example.com', 'password': ''}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrive_user_unauthorized(self):
        """ test authentication is required for user"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """TEST API requests that requires authentication"""
    
    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='testpass123',
            name="Test Name"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrive_profile_success(self):
        """TEST retrieving profile for logged in user"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name':self.user.name,
            'email':self.user.email,
        })

    def test_post_me_not_allowed(self):
        ''' Test POST is not allowed on the me endpoint'''
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for authenticated users."""

        payload = {'name':'Updated Name','password':'newpass123'}
        res = self.client.patch(ME_URL,payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
