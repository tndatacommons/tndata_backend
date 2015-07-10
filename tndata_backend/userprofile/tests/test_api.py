import hashlib

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APITestCase

from .. models import UserProfile
from .. serializers import UserSerializer
from .. import utils


class TestUserSerializer(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="me",
            email="me@example.com",
            password="secret"
        )

    def tearDown(self):
        self.User.objects.all().delete()

    def test_serialize_queryset(self):
        """Run a QuerySet thru the serializer to ensure it doesn't explode."""
        users = self.User.objects.all()
        s = UserSerializer(users, many=True)
        self.assertEqual(len(s.data), 1)  # Should contain data for 1 user
        self.assertEqual(s.data[0]['id'], self.user.id)

    def test_serialize_object(self):
        """Run a Single instance thru the serializer."""
        s = UserSerializer(self.user)
        self.assertIn('id', s.data)
        self.assertEqual(s.data['id'], self.user.id)

    def test_deserialize_partial(self):
        """Ensure that partial serialization works: this is needed for updates
        for models, which may exclude some required fields."""
        data = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'is_staff': False,
            'first_name': "Test",
            'last_name': "User",
        }
        s = UserSerializer(self.user, data=data, partial=True)
        self.assertTrue(s.is_valid())
        self.assertEqual(s.validated_data['username'], "me")


class TestUsersAPI(APITestCase):

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="me",
            email="me@example.com",
            password="secret"
        )

    def tearDown(self):
        self.User.objects.all().delete()

    def test_get_user_list_unauthenticated(self):
        """Ensure unauthenticated requests don't return any data."""
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_get_user_list_authenticated(self):
        """Ensure authenticated requests DO return data."""
        url = reverse('user-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # There should also be a section for categories, goals, behaviors, actions
        self.assertIn('goals', response.data['results'][0])
        self.assertIn('behaviors', response.data['results'][0])
        self.assertIn('actions', response.data['results'][0])
        self.assertIn('categories', response.data['results'][0])

    def test_post_user_list(self):
        """POSTing to the user-list should create a new user."""
        url = reverse('user-list')
        response = self.client.post(url, {'username': 'new', 'password': 'secret'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.User.objects.count(), 2)

        # Ensure retrieved info contains an auth token
        u = self.User.objects.get(username='new')
        self.assertEqual(response.data['username'], 'new')
        self.assertEqual(response.data['token'], u.auth_token.key)

        # Clean up.
        u.delete()

    def test_post_user_list_email_only(self):
        """POSTing to the user-list with a minimum of an email/password should
        create a new user, with that email address"""
        url = reverse('user-list')
        data = {'email': 'new@example.com', 'password': 'secret'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.User.objects.count(), 2)

        # Ensure retrieved info contains an auth token and the expected email
        # and generated username.
        m = hashlib.md5()
        m.update("new@example.com".encode("utf8"))
        expected_username = m.hexdigest()[:30]

        u = self.User.objects.get(email='new@example.com')
        self.assertEqual(u.username, expected_username)
        self.assertEqual(u.email, "new@example.com")
        self.assertEqual(response.data['username'], expected_username)
        self.assertEqual(response.data['token'], u.auth_token.key)

        # Clean up.
        u.delete()

    def test_post_user_list_with_existing_account(self):
        """POSTing to the user-list with username/email for an existing account
        should fail to create a new user, but should return an http 400 response.

        """
        # Generate an existing user.
        user = {"email": "foo@example.com", "first_name": "F", "last_name": "L"}
        user['username'] = utils.username_hash(user['email'])
        user = self.User.objects.create(**user)

        url = reverse('user-list')
        expected_error = "This user account already exists."

        # First try to create with an existing email
        data = {'email': user.email, 'password': 'xxx'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertContains(response, expected_error, status_code=400)

        # Then with an existing username
        data = {'username': user.username, 'password': 'xxx'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertContains(response, expected_error, status_code=400)

    def test_get_user_detail(self):
        """Ensure authenticated users can access their data."""
        url = reverse('user-detail', args=[self.user.id])
        # Include an appropriate `Authorization:` header on all requests.
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_user_detail_unauthorized(self):
        """Ensure unauthenticated users cannot access user detail data."""
        url = reverse('user-detail', args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_auth_token_get_not_allowed(self):
        """GET Requests for the auth token are not allowed."""
        url = reverse("auth-token")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_auth_token_retrieval_with_username(self):
        """Ensure a user can retrieve their auth token by providing their
        username/password."""
        url = reverse("auth-token")
        data = {'username': 'me', 'password': 'secret'}
        response = self.client.post(url, data)
        self.assertEqual(response.data['token'], self.user.auth_token.key)

    def test_auth_token_retrieval_with_email(self):
        """Ensure a user can retrieve their auth token by providing their
        email/password."""
        url = reverse("auth-token")
        data = {'email': 'me@example.com', 'password': 'secret'}
        response = self.client.post(url, data)
        self.assertEqual(response.data['token'], self.user.auth_token.key)


class TestUserProfilesAPI(APITestCase):

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="me",
            email="me@example.com",
            password="secret"
        )
        self.p = self.user.userprofile

    def tearDown(self):
        self.User.objects.all().delete()
        UserProfile.objects.all().delete()

    def test_get_userprofile_list(self):
        """Ensure unauthenticated requests don't return any data."""
        url = reverse('userprofile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_post_userprofile_list_not_allowed(self):
        """POSTing to the userprofile-list should not be allowed."""
        url = reverse('userprofile-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Not allowed Even when authorized.
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_userprofile_detail_unauthorized(self):
        """Ensure unauthenticated users cannot access user detail data."""
        url = reverse('userprofile-detail', args=[self.p.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_userprofile_detail(self):
        """Ensure authenticated users can access their data."""
        url = reverse('userprofile-detail', args=[self.p.id])
        # Include an appropriate `Authorization:` header on all requests.
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user.userprofile.id)
        self.assertEqual(response.data['user'], self.user.id)
        self.assertEqual(response.data['bio'], [])

    def test_post_userprofile_detail_not_allowed(self):
        """Ensure we cannot post to userprofile-detail"""
        url = reverse('userprofile-detail', args=[self.p.id])
        response = self.client.post(url, {'race': "Don't ask"})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Even when authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {'race': "Don't ask"})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_userprofile_detail(self):
        """Test updating userprofiles (e.g. timezones)"""
        url = reverse('userprofile-detail', args=[self.p.id])
        data = {'timezone': "America/New_York"}

        # Not without authentication
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # OK when authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
