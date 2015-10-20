from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from .. models import Place, Token, UserPlace, UserProfile


class TestPlace(TestCase):
    """Tests for the `Place` model. NOTE: We have a migration that creates
    Home, Work, School places."""

    def setUp(self):
        self.place = Place.objects.create(name='Foo')

    def test__str__(self):
        self.assertEqual("{}".format(self.place), "Foo")

    def test_save(self):
        """Ensure that slugs get created on save."""
        self.assertEqual(self.place.slug, "foo")  # From the setUp
        self.place.name = "Foo Thingy"
        self.place.save()
        self.assertEqual(self.place.slug, "foo-thingy")


class TestUserPlace(TestCase):
    """Tests for the `UserPlace` model."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="me",
            email="me@example.com",
            password="secret"
        )
        cls.profile = cls.user.userprofile
        cls.place = Place.objects.get(name="Home")  # from migration
        cls.up = UserPlace.objects.create(
            user=cls.user,
            profile=cls.profile,
            place=cls.place,
            latitude="35.1213",
            longitude="-89.9905"
        )

    def test__str__(self):
        expected = "Home (35.1213, -89.9905)"
        actual = "{}".format(self.up)
        self.assertEqual(expected, actual)

    def test_latlon(self):
        expected = ('35.1213','-89.9905')
        self.assertEqual(self.up.latlon, expected)


class TestUserProfile(TestCase):
    """Tests for the `UserProfile` model."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="me",
            email="me@example.com",
            password="secret"
        )

    def tearDown(self):
        self.user.delete()

    def test__str__(self):
        expected = "me"
        actual = "{}".format(self.user)
        self.assertEqual(expected, actual)

    def test_default_needs_onboarding(self):
        self.assertTrue(self.user.userprofile.needs_onboarding)

    def test_bio(self):
        self.assertEqual(self.user.userprofile.bio, [])

    def test_surveys(self):
        # We didn't create any surveys.
        profile = self.user.userprofile
        self.assertEqual(profile.surveys, {})

    def test_profile_created(self):
        """Ensure creating a user creates a profile."""
        self.assertEqual(UserProfile.objects.filter(user=self.user).count(), 1)

    def test_token_created(self):
        """Ensure creating a user creates an auth token."""
        self.assertEqual(Token.objects.filter(user=self.user).count(), 1)
