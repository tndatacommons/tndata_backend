from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase


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

    def test_get_user_list(self):
        """Ensure unauthenticated requests don't return any data."""
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

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

    def test_auth_token_retrieval(self):
        """Ensure a user can retrieve their auth token."""
        url = reverse("auth-token")
        data = {'username': 'me', 'password': 'secret'}
        response = self.client.post(url, data)
        self.assertEqual(response.data['token'], self.user.auth_token.key)
