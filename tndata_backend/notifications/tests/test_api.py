from datetime import datetime
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from utils.user_utils import hash_value

from .. models import (
    GCMDevice,
    GCMMessage,
)
from .. import queue


User = get_user_model()

DRF_DT_FORMAT = settings.REST_FRAMEWORK['DATETIME_FORMAT']
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
    'DATETIME_FORMAT': DRF_DT_FORMAT,
}


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestGCMDeviceAPI(APITestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        queue.clear()

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('gcm', 'gcm@example.com', 'pass')
        cls.device = GCMDevice.objects.create(
            user=cls.user,
            registration_id="REGISTRATIONID",
            device_name='MYDEVICE',
            device_id=hash_value('gcm@example.com+MYDEVICE'),
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
        self.assertEqual(c['device_id'], self.device.device_id)
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
        post_data = {'registration_id': 'NEWREGID', 'device_name': 'OTHERDEVICE'}
        response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        qs = GCMDevice.objects.filter(user=self.user, registration_id='NEWREGID')
        self.assertTrue(qs.exists())

    def test_post_device_list_updating_device_name(self):
        """Test Updating a Device."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        post_data = {'registration_id': 'NEWREGID', 'device_name': 'MYDEVICE'}
        response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
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


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TestGCMMessageAPI(APITestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        queue.clear()

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
        cls.detail_url = reverse('gcmmessage-detail', args=[cls.message.id])
        cls.payload = {'snooze': 24}  # The only payload allowed is for snoozing.

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
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_message_snooze(self):
        """Ensure the api allows us to snooze a notification."""
        with patch('notifications.models.timezone') as mock_tz:
            mock_tz.now.return_value = datetime(2015, 9, 1, 12, 34)
            self.client.credentials(
                HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
            )
            response = self.client.put(self.detail_url, self.payload)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                response.data['deliver_on'],
                '2015-09-02 12:34:00+0000'
            )
