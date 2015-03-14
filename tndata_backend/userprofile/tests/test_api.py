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

    def test_post_user_list_email_only(self):
        """POSTing to the user-list with a minimum of an email/password should
        create a new user, with that email address"""
        url = reverse('user-list')
        data = {'email': 'new@example.com', 'password': 'secret'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.User.objects.count(), 2)

        # Ensure retrieved info contains an auth token
        u = self.User.objects.get(email='new@example.com')
        self.assertEqual(u.username, u.email)  # username gets set, too
        self.assertEqual(response.data['username'], 'new@example.com')
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

    def test_get_userprofile_list(self):
        """Ensure unauthenticated requests don't return any data."""
        url = reverse('userprofile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    #def test_post_userprofile_list_unauthorized(self):
        #"""POSTing to the userprofile-list should not be allowed."""
        #url = reverse('userprofile-list')
        #response = self.client.post(url, {})
        #self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

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
        self.assertEqual(response.data['home_zip'], '')  # was never set

    # TODO: POST cuases a db error; restrict it.
    # see: http://stackoverflow.com/questions/23639113/disable-a-method-in-a-viewset-django-rest-framework
    #def test_post_userprofile_detail_not_allowed(self):
        #"""Ensure we cannot post to userprofile-detail"""
        #url = reverse('userprofile-detail', args=[self.p.id])
        #response = self.client.post(url, {'home_zip': '12345'})
        #self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_userprofile_detail_unauthorized(self):
        """Ensure unauthenticated users cannot update data."""
        url = reverse('userprofile-detail', args=[self.p.id])
        response = self.client.put(url, {'home_zip': '12345'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # TODO
    #def test_put_userprofile_detail(self):
        #"""Ensure authenticated users can update their data."""
        #url = reverse('userprofile-detail', args=[self.p.id])
        ## Include an appropriate `Authorization:` header on all requests.
        #self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key)
        #response = self.client.post(url, {'home_zip': '12345'})

        #self.assertEqual(response.status_code, status.HTTP_200_OK)
        #self.assertEqual(response.data['home_zip'], '12345')  # updated!
