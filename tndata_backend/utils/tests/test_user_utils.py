from datetime import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import TestCase

import pytz

from .. user_utils import (
    create_inactive_user,
    local_day_range,
    local_now,
    to_localtime,
    to_utc,
    tzdt,
    username_hash,
)


class TestUserUtils(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # Ensure we have a User and they have a profile with a knows timezone
        User = get_user_model()
        cls.user = User.objects.create_user('ty', 'ty@example.com', 'secret')
        cls.profile = cls.user.userprofile
        cls.profile.timezone = 'America/Chicago'
        cls.profile.save()

        # Keep a timezone object on the class for the user's timzone.
        cls.tz = pytz.timezone('America/Chicago')

    def test_tzdt(self):
        # With a default UTC timzone.
        expected = timezone.make_aware(datetime(2015, 1, 15, 13, 30), timezone.utc)
        result = tzdt(2015, 1, 15, 13, 30)
        self.assertEqual(expected, result)

        # With a specified timzone; CST
        expected = timezone.make_aware(datetime(2015, 1, 15, 13, 30), self.tz)
        result = tzdt(2015, 1, 15, 13, 30, tz=self.tz)
        self.assertEqual(expected, result)

    def test_to_utc(self):
        # shouldn't do anything with UTC
        t = timezone.now()
        result = to_utc(t)
        self.assertEqual(result.tzname(), 'UTC')
        self.assertEqual(t, result)

        # should convert naive to UTC
        t = datetime.now()
        self.assertTrue(timezone.is_naive(t))
        result = to_utc(t)
        self.assertTrue(timezone.is_aware(result))
        self.assertEqual(result.tzname(), 'UTC')

        # should convert non-utc to UTC
        t = timezone.make_aware(datetime.now(), timezone=self.tz)
        result = to_utc(t)
        self.assertEqual(result.tzname(), 'UTC')

    def test_to_localtime(self):
        # If give a naive datetime, should convert to the user's timezone.
        dt = datetime(2015, 1, 15, 11, 30)
        result = to_localtime(dt, self.user)
        self.assertEqual(result.tzname(), 'CST')
        self.assertEqual(result, tzdt(2015, 1, 15, 11, 30, tz=self.tz))

        # If given an aware datetime, should convert to the user's timezone
        dt = tzdt(2015, 1, 15, 19, 30)  # 7:30pm UTC -> 1:30pm CST
        result = to_localtime(dt, self.user)
        expected = tzdt(2015, 1, 15, 13, 30, tz=self.tz)
        self.assertEqual(result.tzname(), 'CST')
        self.assertEqual(result.strftime("%c"), expected.strftime("%c"))

    def test_local_now(self):
        with patch('utils.user_utils.timezone') as mock_tz:
            mock_tz.is_aware = timezone.is_aware
            mock_tz.is_naive = timezone.is_naive
            mock_tz.make_naive = timezone.make_naive
            mock_tz.make_aware = timezone.make_aware
            mock_tz.utc = timezone.utc

            # 0am utc -> previous day at 6pm cst
            mock_tz.now.return_value = tzdt(2015, 1, 15, 0, 0)
            expected = tzdt(2015, 1, 14, 18, 0, tz=self.tz)
            result = local_now(self.user)
            self.assertEqual(result.strftime("%c %z"), expected.strftime("%c %z"))

            # 3am utc -> previous day 9pm cst
            mock_tz.now.return_value = tzdt(2015, 1, 15, 3, 0)
            expected = tzdt(2015, 1, 14, 21, 0, tz=self.tz)
            result = local_now(self.user)
            self.assertEqual(result.strftime("%c"), expected.strftime("%c"))

            # 7am utc -> 1am cst
            mock_tz.now.return_value = tzdt(2015, 1, 15, 7, 0)
            expected = tzdt(2015, 1, 15, 1, 0, tz=self.tz)
            result = local_now(self.user)
            self.assertEqual(result.strftime("%c"), expected.strftime("%c"))

            # noon utc -> 6am cst
            mock_tz.now.return_value = tzdt(2015, 1, 15, 12, 0)
            expected = tzdt(2015, 1, 15, 6, 0, tz=self.tz)
            result = local_now(self.user)
            self.assertEqual(result.strftime("%c"), expected.strftime("%c"))

            # 2pm utc -> 8am cst
            mock_tz.now.return_value = tzdt(2015, 1, 15, 14, 0)
            expected = tzdt(2015, 1, 15, 8, 0, tz=self.tz)
            result = local_now(self.user)
            self.assertEqual(result.strftime("%c"), expected.strftime("%c"))

            # 6pm utc -> 12pm cst
            mock_tz.now.return_value = tzdt(2015, 1, 15, 18, 0)
            expected = tzdt(2015, 1, 15, 12, 0, tz=self.tz)
            result = local_now(self.user)
            self.assertEqual(result.strftime("%c"), expected.strftime("%c"))

            # 10pm utc -> 4pm cst
            mock_tz.now.return_value = tzdt(2015, 1, 15, 22, 0)
            expected = tzdt(2015, 1, 15, 16, 0, tz=self.tz)
            result = local_now(self.user)
            self.assertEqual(result.strftime("%c"), expected.strftime("%c"))

            # Next Day 0am utc -> 6pm cst
            mock_tz.now.return_value = tzdt(2015, 1, 16, 0, 0)
            expected = tzdt(2015, 1, 15, 18, 0, tz=self.tz)
            result = local_now(self.user)
            self.assertEqual(result.strftime("%c"), expected.strftime("%c"))

            # Next Day 2am utc -> 8pm cst
            mock_tz.now.return_value = tzdt(2015, 1, 16, 2, 0)
            expected = tzdt(2015, 1, 15, 20, 0, tz=self.tz)
            result = local_now(self.user)
            self.assertEqual(result.strftime("%c"), expected.strftime("%c"))

            # Next Day 2am utc -> 11pm cst
            mock_tz.now.return_value = tzdt(2015, 1, 16, 5, 0)
            expected = tzdt(2015, 1, 15, 23, 0, tz=self.tz)
            result = local_now(self.user)
            self.assertEqual(result.strftime("%c"), expected.strftime("%c"))

    def test_username_hash(self):
        self.assertEqual(
            username_hash('foo@example.com'),
            'b48def645758b95537d4424c84d1a9'
        )

    def test_local_day_range(self):
        with patch('utils.user_utils.timezone') as mock_tz:
            mock_tz.is_aware = timezone.is_aware
            mock_tz.is_naive = timezone.is_naive
            mock_tz.make_naive = timezone.make_naive
            mock_tz.make_aware = timezone.make_aware
            mock_tz.utc = timezone.utc
            mock_tz.now.return_value = tzdt(2015, 10, 1, 11, 30)

            result = local_day_range(self.user)
            expected = (
                tzdt(2015, 10, 1, 5, 0),
                tzdt(2015, 10, 2, 4, 59, 59, 999999)
            )
            self.assertEqual(result, expected)

    def test_create_inactive_user(self):
        user = create_inactive_user("somenewuser@example.com")
        self.assertFalse(user.is_active)
        self.assertTrue(user.userprofile.needs_onboarding)

    def test_create_inactive_user_with_existing_account(self):
        # Note: ty@example.com exists.
        user = create_inactive_user("TY@example.com")

        # existing users shouldn't be altered
        self.assertTrue(user.is_active)

        # This should have just returned the existing account
        self.assertEqual(user.id, self.user.id)
