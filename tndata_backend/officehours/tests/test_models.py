from datetime import time

from django.contrib.auth import get_user_model
from django.test import TestCase

from model_mommy import mommy

from .. models import Course, OfficeHours, generate_course_code


class TestOfficeHours(TestCase):
    """Tests for the `OfficeHours` model."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user('teacher', 't@ch.com', 'pass')
        self.hours = mommy.make(
            OfficeHours,
            from_time=time(13, 30),
            to_time=time(15, 30),
            days=['Monday', 'Wednesday', 'Friday']
        )

    def test__str__(self):
        expected = "13:30 - 15:30 MWF"
        actual = "{}".format(self.hours)
        self.assertEqual(expected, actual)

    def test_expires(self):
        """Expiration date should be 150 days later."""
        delta = self.hours.expires_on - self.hours.created_on
        self.assertEqual(delta.days, 150)


class TestCourse(TestCase):
    """Tests for the `Course` model."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user('teacher', 't@ch.com', 'pass')
        self.course = mommy.make(
            Course,
            name="TEST1234",
            start_time=time(13, 30),
            location="Room 123",
            days=['Monday', 'Wednesday', 'Friday'],
        )

    def test__str__(self):
        expected = "Test1234"
        actual = "{}".format(self.course)
        self.assertEqual(expected, actual)

    def test_display_time(self):
        self.assertEqual(
            self.course.display_time(),
            "1:30 PM"
        )

    def test_code(self):
        # ensure the code is set.
        self.assertEqual(len(self.course.code), 4)

        # test the generate function
        code = generate_course_code()
        self.assertEqual(len(code), 4)
