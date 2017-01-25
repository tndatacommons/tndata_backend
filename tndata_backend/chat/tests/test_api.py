from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import override_settings
from django.utils import timezone

from model_mommy import mommy
from rest_framework import status
from rest_framework.test import APITestCase

from .. models import ChatMessage


# XXX We've got each test case in this module decorated with `override_settings`,
# XXX though I'm not sure that actually works with APITestCase
# XXX See: https://github.com/tomchristie/django-rest-framework/issues/2466
DRF_DT_FORMAT = settings.REST_FRAMEWORK['DATETIME_FORMAT']
TEST_SESSION_ENGINE = 'django.contrib.sessions.backends.db'
TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
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


class V2APITestCase(APITestCase):
    """A parent class for the following test case that reverses a url and
    appends `?version=2`.

    """
    def get_url(self, name, args=None):
        return reverse(name, args=args) + '?version=2'


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestChatMessagesAPI(V2APITestCase):

    def setUp(self):
        self.User = get_user_model()
        self.teacher = self.User.objects.create_user('teacher', 't@x.x', 'pass')
        self.student = self.User.objects.create_user('student', 's@x.x', 'pass')

        self.message_1 = mommy.make(
            ChatMessage,
            user=self.teacher,
            text="Message 1",
            room="chat-{}-{}".format(self.teacher.id, self.student.id)
        )
        self.message_2 = mommy.make(
            ChatMessage,
            user=self.teacher,
            text="Message 2",
            room="chat-{}-{}".format(self.teacher.id, self.student.id)
        )
        self.message_3 = mommy.make(
            ChatMessage,
            user=self.student,
            text="Message 3",
            room="chat-{}-{}".format(self.teacher.id, self.student.id)
        )

    def test_get_list_messages_unauthed(self):
        url = self.get_url('chatmessage-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_list_messages_authed(self):
        # List messages authored by the authenticated user.
        url = self.get_url('chatmessage-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.teacher.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # and the *other* user
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.student.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_get_message_detail_unauthed(self):
        url = self.get_url('chatmessage-detail', args=[self.message_1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_message_detail_authed(self):
        url = self.get_url('chatmessage-detail', args=[self.message_1.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.teacher.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.message_1.id)

    def test_get_history(self):
        # Show chat room history for the teacher...
        room = 'chat-{}-{}'.format(self.teacher.id, self.student.id)
        url = self.get_url('chatmessage-history') + '&room={}'.format(room)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.teacher.auth_token.key
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should include all 3 messages.
        self.assertEqual(response.data['count'], 3)

        # Now test for the student.
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.student.auth_token.key
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should include all 3 messages.
        self.assertEqual(response.data['count'], 3)

    def test_get_history_filters(self):
        # this is just a smoke test for the before/since filters.
        room = 'chat-{}-{}'.format(self.teacher.id, self.student.id)
        url = self.get_url('chatmessage-history')

        now = timezone.now()
        before = now.strftime("%Y-%m-%d %H:%M:%S")
        since = (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        url = '{}&room={}&before={}&since={}'.format(url, room, before, since)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.teacher.auth_token.key
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should include all 3 messages.
        self.assertEqual(response.data['count'], 3)

    def test_get_unread(self):
        url = self.get_url('chatmessage-unread')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.teacher.auth_token.key
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should include all 3 messages.
        self.assertEqual(response.data['count'], 3)

    def test_put_read(self):
        """Test PUT requests to mark messages as read."""

        # Create an unread message in a new room.
        room = "chat-{}-test".format(self.student.id)
        mommy.make(
            ChatMessage,
            user=self.student,
            text="Test Message",
            room=room
        )

        # pre-condition
        messages = ChatMessage.objects.filter(room=room)
        self.assertEqual(messages.filter(read=False).count(), 1)

        # PUT request should mark the room as read and return a 204
        url = self.get_url('chatmessage-read')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.student.auth_token.key
        )
        response = self.client.put(url, {'room': room})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # post-condition
        self.assertEqual(messages.filter(read=True).count(), 0)
