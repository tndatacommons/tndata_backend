from datetime import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import Client, TestCase, override_settings
from model_mommy import mommy

from .. models import Course, OfficeHours


TEST_SESSION_ENGINE = 'django.contrib.sessions.backends.db'
TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
TEST_RQ_QUEUES = settings.RQ_QUEUES.copy()
TEST_RQ_QUEUES['default']['ASYNC'] = False


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestIndexView(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        cls.user = User.objects.create_user('teacher', 't@ch.com', 'pass')

        cls.hours = mommy.make(
            OfficeHours,
            user=cls.user,
        )
        cls.course = mommy.make(
            Course,
            user=cls.user,
            name="TEST1234",
            start_time=time(13, 30),
            location="Room 123",
            days=['Monday', 'Wednesday', 'Friday'],
        )

    def setUp(self):
        self.ua_client = Client()  # An Unauthenticated client
        self.client.login(username="teacher", password="pass")

    def test_get_index(self):
        self.url = reverse("officehours:index")

        # Un-authed should redirect to login
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.get('Location'), reverse('officehours:login'))

        # Authed should redirect to schedule
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.get('Location'), reverse('officehours:schedule'))

    def test_get_login(self):
        self.url = reverse("officehours:login")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('officehours:schedule'))

    def test_get_add_code(self):
        self.url = reverse("officehours:add-code")

        # Un-authed
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    # TODO: needs more view tests
