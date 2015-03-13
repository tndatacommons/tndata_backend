from django.contrib.auth import get_user_model
from django.test import TestCase

from .. models import Token, UserProfile


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

    def test_profile_created(self):
        """Ensure creating a user creates a profile."""
        self.assertEqual(UserProfile.objects.filter(user=self.user).count(), 1)

    def test_token_created(self):
        """Ensure creating a user creates an auth token."""
        self.assertEqual(Token.objects.filter(user=self.user).count(), 1)
