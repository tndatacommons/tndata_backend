import hashlib
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from .. models import Place, UserPlace, UserProfile
from .. serializers import UserSerializer
from utils import user_utils

TEST_REST_FRAMEWORK = {
    'PAGE_SIZE': 100,
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'utils.api.BrowsableAPIRendererWithoutForms',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'utils.api.NoThrottle',
    ),
    'VERSION_PARAM': 'version',
    'DEFAULT_VERSION': '1',
    'ALLOWED_VERSIONS': ['1', '2'],
    'DEFAULT_VERSIONING_CLASS': 'utils.api.DefaultQueryParamVersioning',
}


class V2APITestCase(APITestCase):
    """A parent class for the following test case that reverses a url and
    appends `?version=2`.

    """
    def get_url(self, name, args=None):
        return reverse(name, args=args) + '?version=2'


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestPlaceAPI(V2APITestCase):
    """Tests for the `Place` api endpoint. NOTE: We have a migration that
    creates Home, Work, School places."""

    def setUp(self):
        self.home = Place.objects.get(name="Home")

    def test_get_place_list(self):
        url = self.get_url('place-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 3)  # Places from Migrations
        c = response.data['results'][0]  # Home should be first.
        self.assertEqual(c['id'], self.home.id)
        self.assertEqual(c['name'], self.home.name)
        self.assertEqual(c['slug'], self.home.slug)
        self.assertTrue(c['primary'])

    def test_post_place_list(self):
        """Ensure this endpoint is read-only."""
        url = self.get_url('place-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_place_detail(self):
        url = self.get_url('place-detail', args=[self.home.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.home.id)
        self.assertEqual(response.data['name'], self.home.name)
        self.assertEqual(response.data['slug'], self.home.slug)
        self.assertTrue(response.data['primary'])

    def test_post_place_detail(self):
        """Ensure this endpoint is read-only."""
        url = self.get_url('place-detail', args=[self.home.id])
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestUserPlaceAPI(V2APITestCase):
    """Tests for the `UserPlace` api endpoint. NOTE: We have a migration that
    creates Home, Work, School places."""

    def setUp(self):
        self.home = Place.objects.get(name="Home")

        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="me",
            email="me@example.com",
            password="secret"
        )
        self.profile = self.user.userprofile
        self.up = UserPlace.objects.create(
            user=self.user,
            profile=self.profile,
            place=self.home,
            latitude="35.1213",
            longitude="-89.9905"
        )

    def test_get_userplace_list_unauthenticated(self):
        """Ensure unauthenticated requests don't return any data."""
        url = self.get_url('userplace-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_get_userplace_list(self):
        url = self.get_url('userplace-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        obj = response.data['results'][0]
        self.assertEqual(obj['id'], self.up.id)
        self.assertEqual(obj['user'], self.user.id)
        self.assertEqual(obj['profile'], self.profile.id)
        self.assertEqual(obj['place']['id'], self.home.id)
        self.assertEqual(obj['place']['name'], self.home.name)
        self.assertEqual(obj['place']['slug'], self.home.slug)

    def test_post_userplace_list(self):
        """Creating an new place should create a new UserPlace and a Place object."""
        url = self.get_url('userplace-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        post_data = {
            'place': 'The Library',
            'latitude': '35.123456789',
            'longitude': '-89.123456789',
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # We should have a new Place.
        self.assertEqual(Place.objects.filter(name="The Library").count(), 1)

        # The user should have a UserPlace object.
        up = UserPlace.objects.get(user=self.user, place__name="The Library")
        self.assertEqual(up.user, self.user)
        self.assertEqual(up.profile, self.profile)
        self.assertEqual(str(up.latitude), "35.1235")
        self.assertEqual(str(up.longitude), "-89.1235")

    def test_post_userplace_list_duplicate_not_allowed(self):
        """Creating an duplicate place name is not allowed."""
        url = self.get_url('userplace-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )

        # NOTE: The user already has a Home place saved (from setUp)
        post_data = {
            'place': 'Home',
            'latitude': '35.123456789',
            'longitude': '-89.123456789',
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_userplace_detail(self):
        """Ensure a user can view their own place data."""
        url = self.get_url('userplace-detail', args=[self.up.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['user'], self.user.id)
        self.assertEqual(response.data['profile'], self.profile.id)
        self.assertEqual(response.data['place']['id'], self.home.id)
        self.assertEqual(response.data['place']['name'], self.home.name)
        self.assertEqual(response.data['place']['slug'], self.home.slug)
        self.assertTrue(response.data['place']['primary'])

    def test_put_userplace_detail(self):
        """Ensure users can update their UserPlace objects."""
        url = self.get_url('userplace-detail', args=[self.up.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        post_data = {'longitude': '20.0'}
        response = self.client.put(url, post_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Now, let's check the result.
        up = UserPlace.objects.get(pk=self.up.id)
        self.assertEqual(str(up.longitude), '20.0000')
        self.assertEqual(str(up.latitude), str(self.up.latitude))  # unchanged


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
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


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestUsersAPI(V2APITestCase):

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
        url = self.get_url('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_get_user_list_authenticated(self):
        """Ensure authenticated requests DO return data."""
        url = self.get_url('user-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # There should also be a section for categories, goals, behaviors, actions
        self.assertIn('user_goals', response.data['results'][0])
        self.assertIn('user_behaviors', response.data['results'][0])
        self.assertIn('user_actions', response.data['results'][0])
        self.assertIn('user_categories', response.data['results'][0])
        self.assertIn('places', response.data['results'][0])

    def test_post_user_list(self):
        """POSTing to the user-list should create a new user."""
        url = self.get_url('user-list')
        data = {'email': 'new@user.com', 'password': 'secret'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.User.objects.count(), 2)

        # Ensure retrieved info contains an auth token
        u = self.User.objects.get(email='new@user.com')
        self.assertEqual(response.data['token'], u.auth_token.key)

        # Clean up.
        u.delete()

    def test_post_user_list_email_only(self):
        """POSTing to the user-list with a minimum of an email/password should
        create a new user, with that email address"""
        url = self.get_url('user-list')
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

    def test_post_user_list_with_existing_account_email_as_username(self):
        """POSTing to the user-list with the email address for an existing account
        (even if provided as the username) should fail to create a new user,
        but should return an http 400 response.

        """
        # Generate an existing user.
        user = {"email": "foo@example.com", "first_name": "F", "last_name": "L"}
        user['username'] = user_utils.username_hash(user['email'])
        user = self.User.objects.create(**user)

        url = self.get_url('user-list')
        expected_error = "This user account already exists."

        # First try to create this account, but include the email in the
        # username field.
        data = {'username': user.email, 'password': 'xxx'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertContains(response, expected_error, status_code=400)

    def test_post_user_list_with_existing_account(self):
        """POSTing to the user-list with username/email for an existing account
        should fail to create a new user, but should return an http 400 response.

        """
        # Generate an existing user.
        user = {"email": "foo@example.com", "first_name": "F", "last_name": "L"}
        user['username'] = user_utils.username_hash(user['email'])
        user = self.User.objects.create(**user)

        url = self.get_url('user-list')
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

    def test_get_user_detail(self):
        """Ensure authenticated users can access their data."""
        url = self.get_url('user-detail', args=[self.user.id])
        # Include an appropriate `Authorization:` header on all requests.
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_user_detail_unauthorized(self):
        """Ensure unauthenticated users cannot access user detail data."""
        url = self.get_url('user-detail', args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_auth_token_get_not_allowed(self):
        """GET Requests for the auth token are not allowed."""
        url = self.get_url("auth-token")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_auth_token_retrieval_with_username(self):
        """Ensure a user can retrieve their auth token by providing their
        username/password."""
        url = self.get_url("auth-token")
        data = {'username': 'me', 'password': 'secret'}
        response = self.client.post(url, data)
        self.assertEqual(response.data['token'], self.user.auth_token.key)

        # Check for some values
        self.assertIn('username', response.data)
        self.assertIn('email', response.data)
        self.assertIn('user_id', response.data)
        self.assertIn('userprofile_id', response.data)
        self.assertIn('first_name', response.data)
        self.assertIn('last_name', response.data)
        self.assertIn('full_name', response.data)
        self.assertIn('token', response.data)
        self.assertIn('needs_onboarding', response.data)

    def test_auth_token_retrieval_with_email(self):
        """Ensure a user can retrieve their auth token by providing their
        email/password."""
        url = self.get_url("auth-token")
        data = {'email': 'me@example.com', 'password': 'secret'}
        response = self.client.post(url, data)
        self.assertEqual(response.data['token'], self.user.auth_token.key)

        # Check for some values
        self.assertIn('username', response.data)
        self.assertIn('email', response.data)
        self.assertIn('user_id', response.data)
        self.assertIn('userprofile_id', response.data)
        self.assertIn('first_name', response.data)
        self.assertIn('last_name', response.data)
        self.assertIn('full_name', response.data)
        self.assertIn('token', response.data)
        self.assertIn('needs_onboarding', response.data)

    def test_get_api_logout_not_allowed(self):
        """Ensure GET requests to the api_logout endpoint are not allowed."""
        url = self.get_url("auth-logout")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_post_api_logout(self):
        """Ensure POST requests to the api_logout endpoint or OK."""
        url = self.get_url("auth-logout")
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        with patch("userprofile.api.logout") as mock_logout:
            response = self.client.post(url, {'foo': 'bar'})
            self.assertTrue(mock_logout.called)
            self.assertEqual(response.status_code, status.HTTP_200_OK)


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestUserProfilesAPI(V2APITestCase):

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

    def test_get_userprofile_list_unauthed(self):
        """Ensure unauthenticated requests don't return any data."""
        url = self.get_url('userprofile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_get_userprofile_list(self):
        """Ensure authenticated requests return the user's data."""
        url = self.get_url('userprofile-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.p.id)
        self.assertEqual(response.data['results'][0]['user'], self.user.id)
        self.assertEqual(response.data['results'][0]['timezone'], self.p.timezone)
        self.assertTrue(response.data['results'][0]['needs_onboarding'])

    def test_post_userprofile_list_not_allowed(self):
        """POSTing to the userprofile-list should not be allowed."""
        url = self.get_url('userprofile-list')
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
        url = self.get_url('userprofile-detail', args=[self.p.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_userprofile_detail(self):
        """Ensure authenticated users can access their data."""
        url = self.get_url('userprofile-detail', args=[self.p.id])
        # Include an appropriate `Authorization:` header on all requests.
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user.userprofile.id)
        self.assertEqual(response.data['user'], self.user.id)
        self.assertEqual(response.data['bio'], [])
        self.assertEqual(response.data['timezone'], self.p.timezone)
        self.assertEqual(response.data['needs_onboarding'], self.p.needs_onboarding)

    def test_post_userprofile_detail_not_allowed(self):
        """Ensure we cannot post to userprofile-detail"""
        url = self.get_url('userprofile-detail', args=[self.p.id])
        response = self.client.post(url, {'race': "Don't ask"})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Even when authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {'race': "Don't ask"})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_userprofile_detail_timezone(self):
        """Test updating userprofiles; timezone-only"""
        url = self.get_url('userprofile-detail', args=[self.p.id])
        data = {'timezone': "America/New_York"}

        # Not without authentication
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # OK when authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, data)
        self.assertEqual(UserProfile.objects.get(pk=self.p.id).timezone, 'America/New_York')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_userprofile_detail_needs_onboarding(self):
        """Test updating userprofiles; needs_onboarding-only"""
        url = self.get_url('userprofile-detail', args=[self.p.id])
        data = {'needs_onboarding': True}

        # Not without authentication
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # OK when authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['needs_onboarding'])

    def test_put_userprofile_detail_all(self):
        """Test updating userprofiles; needs_onboarding-only"""
        url = self.get_url('userprofile-detail', args=[self.p.id])
        data = {
            'timezone': "America/New_York",
            'needs_onboarding': True,
        }

        # Not without authentication
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # OK when authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['timezone'], "America/New_York")
        self.assertTrue(response.data['needs_onboarding'])


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestSimpleProfileAPI(V2APITestCase):

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="me",
            email="me@example.com",
            password="secret"
        )
        self.profile = self.user.userprofile

    def tearDown(self):
        self.User.objects.all().delete()
        UserProfile.objects.all().delete()

    def test_defaults(self):
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.timezone, 'America/Chicago')
        self.assertEqual(self.profile.maximum_daily_notifications, 3)
        self.assertEqual(self.profile.needs_onboarding, True)
        self.assertIsNone(self.profile.zipcode)
        self.assertIsNone(self.profile.birthday)
        self.assertEqual(self.profile.sex, "")
        self.assertFalse(self.profile.employed)
        self.assertFalse(self.profile.is_parent)
        self.assertFalse(self.profile.in_relationship)
        self.assertFalse(self.profile.has_degree)

    def test_get_unauthed(self):
        url = self.get_url('profile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_get_authed(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        url = self.get_url('profile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_get_detail_unauthed(self):
        url = self.get_url('profile-detail', args=[self.profile.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_detail_authed(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        url = self.get_url('profile-detail', args=[self.profile.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_list_not_allowed(self):
        """POSTing to the profile-list should not be allowed."""
        url = self.get_url('profile-list')
        response = self.client.post(url, {})
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

        # Not allowed Even when authorized.
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_profile(self):
        """Test updating userprofiles w/ all data"""
        url = self.get_url('profile-detail', args=[self.profile.id])
        payload = {
            'timezone': "America/New_York",
            'maximum_daily_notifications': 42,
            'needs_onboarding': False,
            'zipcode': '12345',
            'birthday': '1999-12-31',
            'sex': 'female',
            'employed': True,
            'is_parent': True,
            'in_relationship': True,
            'has_degree': True,
        }

        # Not without authentication
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # OK when authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        profile = UserProfile.objects.get(pk=self.profile.id)
        self.assertEqual(profile.timezone, 'America/New_York')
        self.assertEqual(profile.maximum_daily_notifications, 42)
        self.assertEqual(profile.zipcode, '12345')
        self.assertEqual(profile.birthday, date(1999, 12, 31))
        self.assertEqual(profile.get_sex_display(), "Female")
        self.assertFalse(profile.needs_onboarding)
        self.assertTrue(profile.employed)
        self.assertTrue(profile.is_parent)
        self.assertTrue(profile.in_relationship)
        self.assertTrue(profile.has_degree)

    def test_put_partial_profile(self):
        """Test updating userprofiles with partial data"""
        url = self.get_url('profile-detail', args=[self.profile.id])
        payload = {
            'timezone': "America/New_York",
            'maximum_daily_notifications': 1,
            'zipcode': '',
            'birthday': '',
            'sex': '',
        }

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        profile = UserProfile.objects.get(pk=self.profile.id)
        self.assertEqual(profile.timezone, 'America/New_York')
        self.assertEqual(profile.maximum_daily_notifications, 1)
        self.assertEqual(profile.zipcode, '')
        self.assertEqual(profile.birthday, None)
        self.assertEqual(profile.get_sex_display(), "Prefer not to answer")
