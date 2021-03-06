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
            schedule={
                'Monday': [
                    ['8:00 am', '10:00 am'],
                    ['12:30 pm', '1:30 pm']
                ],
                'Wednesday': [
                    ['8:00 am', '10:00 am'],
                ]
            }
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
            'schedule': {
                'Friday': [['5:30 pm', '6:30 pm']],
            }
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check the object.
        hours = OfficeHours.objects.get(pk=response.data['id'])
        self.assertEqual(hours.days, ['Friday'])
        self.assertDictEqual(hours.schedule, data['schedule'])

    def test_post_hours_authed_alternative(self):
        url = self.get_url('officehours-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = {
            'meetingtime': 'TRZ 13:30-14:30',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check the object.
        hours = OfficeHours.objects.get(pk=response.data['id'])
        self.assertDictEqual(
            hours.schedule,
            {
                'Tuesday': [['13:30', '14:30']],
                'Thursday': [['13:30', '14:30']],
                'Saturday': [['13:30', '14:30']],
            }
        )

    def test_put_hours_authed(self):
        hours = mommy.make(
            OfficeHours,
            user=self.user,
            schedule={
                'Monday': [
                    ['8:00 am', '10:00 am'],
                    ['12:30 pm', '1:30 pm']
                ],
                'Wednesday': [
                    ['8:00 am', '10:00 am'],
                ]
            }
        )

        url = self.get_url('officehours-detail', args=[hours.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = {
            'schedule': {'Saturday': [['1:00 pm', '2:00 pm']]}
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the object.
        hours = OfficeHours.objects.get(pk=hours.id)
        self.assertDictEqual(hours.schedule, data['schedule'])

    def test_put_hours_authed_alternative(self):
        hours = mommy.make(OfficeHours, user=self.user)
        url = self.get_url('officehours-detail', args=[hours.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, {'meetingtime': 'MWR 13:30-15:30'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the object.
        hours = OfficeHours.objects.get(pk=response.data['id'])

        expected = ['Monday', 'Wednesday', 'Thursday']
        self.assertEqual(hours.days, expected)
        self.assertDictEqual(
            hours.schedule,
            {
                'Monday': [['13:30', '15:30']],
                'Wednesday': [['13:30', '15:30']],
                'Thursday': [['13:30', '15:30']],
            }
        )


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
        self.assertEqual(
            response.data['results'][0]['meetingtime'],
            'MF 13:30'
        )

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

    def test_post_course_authed_alternative_no_ending(self):
        """Test that createing a Course supports `MTWRFS H:mm`-formatted
        days + start time for courses."""

        url = self.get_url('course-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = {
            'name': 'Test Afternoon Course',
            'location': 'Location',
            'meetingtime': 'RZ 14:30',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check the object's values
        course = Course.objects.get(pk=response.data['id'])
        expected = sorted(['Thursday', 'Saturday'])
        self.assertEqual(sorted(course.days), expected)
        self.assertEqual(course.start_time.strftime("%H:%M"), "14:30")

    def test_put_course_authed(self):
        course = mommy.make(
            Course,
            user=self.user,
            name="TEST-9999",
            start_time=time(10, 30),
            location="Room 123",
            days=['Sunday', 'Saturday']
        )

        url = self.get_url('course-detail', args=[course.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = {
            'name': 'Intro to Testing',  # Changed
            'days': ['Monday', 'Friday'],  # Changed
            'location': 'Room 123',
            'start_time': '10:30',
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the object.
        course = Course.objects.get(pk=course.id)
        self.assertEqual(course.name, 'Intro to Testing')
        expected_days = sorted(['Monday', 'Friday'])
        self.assertEqual(sorted(course.days), expected_days)
        self.assertEqual(course.start_time.strftime("%H:%M"), "10:30")

    def test_put_course_authed_alternative(self):
        course = mommy.make(
            Course,
            user=self.user,
            name="TEST-9999",
            start_time=time(10, 30),
            location="Room 123",
            days=['Sunday', 'Saturday']
        )

        url = self.get_url('course-detail', args=[course.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = {
            'name': 'TEST-9999',
            'location': 'Room 123',
            'meetingtime': 'MWR 13:30-15:30',  # Changed
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the object.
        course = Course.objects.get(pk=course.id)
        expected_days = sorted(['Monday', 'Wednesday', 'Thursday'])
        self.assertEqual(sorted(course.days), expected_days)
        self.assertEqual(course.start_time.strftime("%H:%M"), "13:30")

    def test_put_course_authed_alternative_no_ending(self):
        course = mommy.make(
            Course,
            user=self.user,
            name="TEST-9999",
            start_time=time(10, 30),
            location="Room 123",
            days=['Sunday', 'Saturday']
        )

        url = self.get_url('course-detail', args=[course.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = {
            'name': 'TEST-9999',
            'location': 'Room 123',
            'meetingtime': 'MWR 16:45',  # Changed
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the object.
        course = Course.objects.get(pk=course.id)
        expected_days = sorted(['Monday', 'Wednesday', 'Thursday'])
        self.assertEqual(sorted(course.days), expected_days)
        self.assertEqual(course.start_time.strftime("%H:%M"), "16:45")

    def test_post_course_enroll(self):
        """Test that students can add a Course to their schedule."""
        # Create a test student.
        student = self.User.objects.create_user('student', 's@s.com', 'pass')

        # Ensure they're NOT in the course
        self.assertNotIn(student, self.course.students.all())

        url = self.get_url('course-enroll')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + student.auth_token.key
        )

        data = {
            'code': self.course.code,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify that the student IS enrolled in the Course.
        self.assertIn(student, self.course.students.all())
