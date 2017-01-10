from datetime import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import override_settings

from model_mommy import mommy
from rest_framework import status
from rest_framework.test import APITestCase

from .. models import Course, OfficeHours


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
class TestOfficeHoursAPI(V2APITestCase):

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user('teacher', 't@ch.com', 'pass')
        self.hours = mommy.make(
            OfficeHours,
            user=self.user,
            from_time=time(13, 30),
            to_time=time(15, 30),
            days=['Monday', 'Wednesday', 'Friday']
        )

    def tearDown(self):
        OfficeHours.objects.filter(id=self.hours.id).delete()

    def test_get_hours_list_unauthed(self):
        url = self.get_url('officehours-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_hours_list_authed(self):
        url = self.get_url('officehours-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_get_hours_detail_unauthed(self):
        url = self.get_url('officehours-detail', args=[self.hours.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_hours_detail_authed(self):
        url = self.get_url('officehours-detail', args=[self.hours.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.hours.id)

    def test_post_hours_authed(self):
        url = self.get_url('officehours-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = {
            'from_time': '13:30',
            'to_time': '14:30',
            'days': ['Tuesday', 'Thursday'],
            'user': self.user.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check the object.
        hours = OfficeHours.objects.get(pk=response.data['id'])
        self.assertEqual(sorted(hours.days), sorted(['Tuesday', 'Thursday']))

    def test_post_hours_authed_alternative(self):
        url = self.get_url('officehours-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = {
            'from_time': '13:30',
            'to_time': '14:30',
            'days': 'TRZ',
            'user': self.user.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check the object.
        hours = OfficeHours.objects.get(pk=response.data['id'])

        expected = sorted(['Tuesday', 'Thursday', 'Saturday'])
        self.assertEqual(sorted(hours.days), expected)

@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestCourseAPI(V2APITestCase):

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user('teacher', 't@ch.com', 'pass')
        self.course = mommy.make(
            Course,
            user=self.user,
            name="TEST1234",
            start_time=time(13, 30),
            location="Room 123",
            days=['Monday', 'Friday']
        )

    def tearDown(self):
        Course.objects.filter(id=self.course.id).delete()

    def test_get_course_list_unauthed(self):
        url = self.get_url('course-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_course_list_authed(self):
        url = self.get_url('course-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_get_course_detail_unauthed(self):
        url = self.get_url('course-detail', args=[self.course.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_course_detail_authed(self):
        url = self.get_url('course-detail', args=[self.course.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.course.id)

    def test_post_course_authed(self):
        url = self.get_url('course-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = {
            'name': 'Morning Course',
            'start_time': '9:30',
            'location': 'Room 0',
            'days': ['Monday', 'Wednesday'],
            'user': self.user.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check the object.
        course = Course.objects.get(pk=response.data['id'])
        self.assertEqual(sorted(course.days), sorted(['Monday', 'Wednesday']))

    def test_post_course_authed_alternative(self):
        """Test that createing a Course supports `MTWRFS H:mm-H:mm`-formatted
        days + start time for courses."""

        url = self.get_url('course-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = {
            'user': self.user.id,
            'name': 'Test Morning Course',
            'location': 'Location',
            'meetingtime': 'MWF 9:30-13:30',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check the object's values
        course = Course.objects.get(pk=response.data['id'])
        expected = sorted(['Monday', 'Wednesday', 'Friday'])
        self.assertEqual(sorted(course.days), expected)
        self.assertEqual(course.start_time.strftime("%H:%M"), "09:30")

