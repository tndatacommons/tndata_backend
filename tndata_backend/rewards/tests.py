from django.test import TestCase
from .models import FunContent


class TestFunContent(TestCase):

    def setUp(self):
        self.quote = FunContent.objects.create(
            message_type='quote',
            message="Here's a quote",
            author="Brad",
            keywords=['foo', 'bar'],
        )

    def test__str__(self):
        expected = "Here's a quote"
        actual = "{}".format(self.quote)
        self.assertEqual(expected, actual)

    def test__clean_keywords(self):
        obj = FunContent(keywords=['   BAZ', 'binGO'])
        obj._clean_keywords()
        self.assertEqual(obj.keywords, ['baz', 'bingo'])


class TestFunContentManager(TestCase):

    def tearDown(self):
        FunContent.objects.all().delete()

    def test_with_exiting_content(self):
        quote = FunContent.objects.create(
            message_type='quote',
            message="Here's a quote",
            author="Brad",
            keywords=['foo', 'bar'],
        )

        obj = FunContent.objects.random()
        self.assertEqual(obj.id, quote.id)

    def test_with_no_content(self):
        """If tehre are no FunContent items this should return None"""
        obj = FunContent.objects.random()
        self.assertIsNone(obj)
