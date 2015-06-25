from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .. models import (
    GCMDevice,
    GCMMessage,
)

User = get_user_model()


class TestGCMDeviceAPI(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('gcm', 'gcm@example.com', 'pass')
        cls.device = GCMDevice.objects.create(
            user=cls.user,
            registration_id="REGISTRATIONID"
        )
        cls.url = reverse('gcmdevice-list')

    def test_get_device_list_unauthenticated(self):
        """Ensure un-authenticated requests don't expose any results."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_get_device_list(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        c = response.data['results'][0]
        self.assertEqual(c['id'], self.device.id)
        self.assertEqual(c['user'], self.device.user.id)
        self.assertEqual(c['device_name'], self.device.device_name)
        self.assertEqual(c['is_active'], self.device.is_active)
        self.assertIn('created_on', c)
        self.assertIn('updated_on', c)

    def test_post_device_list_unauthenticated(self):
        """Ensure this endpoint requires authorization."""
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_device_list(self):
        """Test Creating a Device."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(self.url, {'registration_id': 'NEWREGID'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        qs = GCMDevice.objects.filter(user=self.user, registration_id='NEWREGID')
        self.assertTrue(qs.exists())

    def test_post_device_list_duplicate(self):
        """Test POSTing a Device with unchanged data."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = {'registration_id': 'REGISTRATIONID'}  # unchanged
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_304_NOT_MODIFIED)

    def test_get_device_detail(self):
        """There is no device detail endpoint."""
        url = "{0}{1}".format(reverse('gcmdevice-list'), self.device.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestGCMMessageAPI(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('gcm', 'gcm@example.com', 'pass')
        cls.device = GCMDevice.objects.create(
            user=cls.user,
            registration_id="REGISTRATIONID"
        )
        cls.message = GCMMessage.objects.create(
            cls.user,
            "Test Title",
            "Test Message",
            datetime.utcnow(),
            obj=cls.device,  # Kind of a hack
        )
        cls.url = reverse('gcmmessage-list')
        cls.detail_url = reverse('gcmmessage-detail', args=[cls.device.id])
        cls.payload = {

        }

    def test_get_message_list_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_message_list(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_message_list_unauthenticated(self):
        """Ensure this endpoint requires authorization."""
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_post_message_list(self):
        """Test Creating a Device."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_message_detail_unauthenticated(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_message_detail(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
