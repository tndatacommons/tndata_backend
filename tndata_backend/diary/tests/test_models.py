from django.test import TestCase
from django.contrib.auth import get_user_model

from .. models import Feeling


class TestFeeling(TestCase):
    """Tests for the `Feeling` model."""

    def setUp(self):
        user_data = {
            'username': 'diary_user',
            'email': 'diary_user@example.com',
            'password': 'secret'
        }
        self.user = get_user_model().objects.create_user(**user_data)

    def test_feeling(self):
        """Ensure we can create a Feeling instance."""
        with self.assertNumQueries(1):
            Feeling.objects.create(
                user=self.user, rank=Feeling.GREAT, notes="Yep"
            )

    def test__str__(self):
        f = Feeling.objects.create(
            user=self.user, rank=Feeling.GREAT, notes="Yep"
        )
        self.assertEqual("Great", "{}".format(f))
