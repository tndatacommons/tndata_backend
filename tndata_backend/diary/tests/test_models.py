from django.test import TestCase
from django.contrib.auth import get_user_model

from .. models import Entry


class TestEntry(TestCase):
    """Tests for the `Entry` model."""

    def setUp(self):
        user_data = {
            'username': 'diary_user',
            'email': 'diary_user@example.com',
            'password': 'secret'
        }
        self.user = get_user_model().objects.create_user(**user_data)

    def test_entry(self):
        """Ensure we can create an Entry instance."""
        with self.assertNumQueries(1):
            Entry.objects.create(
                user=self.user, rank=Entry.GREAT, notes="Yep"
            )

    def test__str__(self):
        f = Entry.objects.create(
            user=self.user, rank=Entry.GREAT, notes="Yep"
        )
        self.assertEqual("Great", "{}".format(f))
