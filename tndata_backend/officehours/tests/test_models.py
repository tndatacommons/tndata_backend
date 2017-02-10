from datetime import time

from django.contrib.auth import get_user_model
from django.test import TestCase

from model_mommy import mommy

from .. models import Course, OfficeHours, generate_course_code


class TestOfficeHours(TestCase):
    """Tests for the `OfficeHours` model."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user('teacher', 't@ch.com', 'pass')
        cls.hours = mommy.make(
            OfficeHours,
            user=cls.user,
            schedule={
                'Monday': [
                    {'from': '8:00 am', 'to': '10:00 am'},
                    {'from': '12:30 am', 'to': '1:30 pm'},
                ],
                'Wednesday': [
                    {'from': '8:00 am', 'to': '10:00 am'},
                ]
            }
        )

    def test__str__(self):
        self.assertTrue(str(self.hours))  # just so it gives us *something*

    def test_expires(self):
        """Expiration date should be 150 days later."""
        delta = self.hours.expires_on - self.hours.created_on
        # i'm lazy, this shoudl be 150 but my not be due to it being based on utc
        self.assertTrue(delta.days >= 149)

    def test_days(self):
        self.assertEqual(self.hours.days, ['Monday', 'Wednesday'])

    def test_get_schedule(self):
        expected = [
            ('Monday', [
                {'from': '8:00 am', 'to': '10:00 am'},
                {'from': '12:30 am', 'to': '1:30 pm'},
            ]),
            ('Wednesday', [
                {'from': '8:00 am', 'to': '10:00 am'},
            ]),
        ]
        self.assertEqual(self.hours.get_schedule(), expected)

    def test_get_absolute_url(self):
        self.assertEqual(
            self.hours.get_absolute_url(),
            '/officehours/hours/{}/'.format(self.hours.pk)
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.hours.get_delete_url(),
            '/officehours/hours/{}/delete/'.format(self.hours.pk)
        )


class TestCourse(TestCase):
    """Tests for the `Course` model."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user('teacher', 't@ch.com', 'pass')
        cls.course = mommy.make(
            Course,
            user=cls.user,
            name="TEST1234",
            start_time=time(13, 30),
            location="Room 123",
            days=['Monday', 'Wednesday', 'Friday'],
        )
        cls.online = mommy.make(
            Course,
            user=cls.user,
            name="Some Online Course"
        )

    def test__str__(self):
        actual = "{}".format(self.course)
        self.assertEqual(actual, "TEST1234")

        actual = "{}".format(self.online)
        self.assertEqual(actual, "Some Online Course")

    def test_display_time(self):
        self.assertEqual(
            self.course.display_time(),
            "01:30PM MWF"
        )

        self.assertEqual(self.online.display_time(), "")

    def test_code(self):
        # ensure the code is set.
        self.assertEqual(len(self.course.code), 4)

        # test the generate function
        code = generate_course_code()
        self.assertEqual(len(code), 4)

    def test_meetingtime(self):
        self.assertEqual(self.course.meetingtime, "MWF 13:30")
        self.assertEqual(self.online.meetingtime, "")


    def test_get_absolute_url(self):
        self.assertEqual(
            self.course.get_absolute_url(),
            "/officehours/schedule/{}/".format(self.course.pk)
        )
        self.assertEqual(
            self.online.get_absolute_url(),
            "/officehours/schedule/{}/".format(self.online.pk)
        )

    def test_get_share_url(self):
        self.assertEqual(
            self.course.get_share_url(),
            "/officehours/schedule/{}/share/".format(self.course.pk)
        )
        self.assertEqual(
            self.online.get_share_url(),
            "/officehours/schedule/{}/share/".format(self.online.pk)
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.course.get_delete_url(),
            "/officehours/schedule/{}/delete/".format(self.course.pk)
        )
        self.assertEqual(
            self.online.get_delete_url(),
            "/officehours/schedule/{}/delete/".format(self.online.pk)
        )

    def test_get_officehours(self):
        self.assertEqual(list(self.course.get_officehours()), [])
