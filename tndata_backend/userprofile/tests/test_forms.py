from django.contrib.auth import get_user_model
from django.test import TestCase
from ..forms import UserForm, UserProfileForm


class TestUserForm(TestCase):

    def test_form(self):
        """Verify form completed and validity with expected data."""
        data = {
            'first_name': "Alpha",
            'last_name': "Centauri",
            'email': "ac@example.com",
        }

        form = UserForm()
        self.assertFalse(form.is_bound)
        self.assertEqual(
            sorted(form.fields.keys()),
            ['email', 'first_name', 'last_name']
        )

        # Test with data
        form = UserForm(data)
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(user.first_name, "Alpha")
        self.assertEqual(user.last_name, "Centauri")
        self.assertEqual(user.email, "ac@example.com")
        self.assertIsNotNone(user.id)

    def test_form_not_valid_with_missing_fields(self):
        """Verify form completed and validity with expected data."""
        form = UserForm({'first_name': '', 'last_name': '', 'email': ''})
        self.assertFalse(form.is_valid())

        form = UserForm({'first_name': 'A', 'last_name': 'B', 'email': 'c'})
        self.assertFalse(form.is_valid())

        form = UserForm({'first_name': 'A', 'last_name': 'B', 'email': ''})
        self.assertFalse(form.is_valid())


class TestUserProfileForm(TestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user('x', 'y@z.co', 'pass')
        self.profile = self.user.userprofile

    def test_form(self):
        """Verify form completed and validity with expected data."""
        # Unbound form
        form = UserProfileForm()
        self.assertFalse(form.is_bound)
        self.assertEqual(
            sorted(form.fields.keys()),
            ['maximum_daily_notifications', 'timezone']
        )

        # Bound Form
        data = {
            'timezone': 'Pacific/Yap',
            'maximum_daily_notifications': 42
        }
        form = UserProfileForm(data, instance=self.profile)
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_valid())

        # Test Saving
        profile = form.save()
        self.assertEqual(profile.timezone, 'Pacific/Yap')
        self.assertEqual(profile.maximum_daily_notifications, 42)
