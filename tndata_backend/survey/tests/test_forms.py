from django.test import TestCase

from .. forms import (
    BinaryQuestionForm,
    LikertQuestionForm,
    MultipleChoiceQuestionForm,
    OpenEndedQuestionForm,
)


class TestBinaryQuestionForm(TestCase):

    def test_unbound(self):
        form = BinaryQuestionForm()
        expected_fields = [
            'available', 'instructions', 'instruments', 'labels', 'order',
            'subscale', 'text',
        ]
        self.assertEqual(
            sorted(list(form.fields.keys())),
            expected_fields
        )

    def test_bound(self):
        form = BinaryQuestionForm({
            'available': True,
            'instructions': 'To do',
            'instruments': '',
            'labels': 'family,health',
            'order': 1,
            'subscale': 0,
            'text': 'Test Question',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['labels'], ['family', 'health'])


class TestLikertQuestionForm(TestCase):

    def test_unbound(self):
        form = LikertQuestionForm()
        expected_fields = [
            'available', 'instructions', 'instruments', 'labels', 'order',
            'priority', 'scale', 'subscale', 'text',
        ]
        self.assertEqual(
            sorted(list(form.fields.keys())),
            expected_fields
        )

    def test_bound(self):
        form = LikertQuestionForm({
            'available': True,
            'instructions': 'To do',
            'instruments': '',
            'labels': 'family,health',
            'order': 1,
            'priority': 0,
            'scale': '5_point_agreement',
            'subscale': 0,
            'text': 'Test Question',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['labels'], ['family', 'health'])


class TestMultipleChoiceQuestionForm(TestCase):

    def test_unbound(self):
        form = MultipleChoiceQuestionForm()
        expected_fields = [
            'available', 'instructions', 'instruments', 'labels', 'order',
            'subscale', 'text',
        ]
        self.assertEqual(
            sorted(list(form.fields.keys())),
            expected_fields
        )

    def test_bound(self):
        form = MultipleChoiceQuestionForm({
            'available': True,
            'instructions': 'To do',
            'instruments': '',
            'labels': 'family,health',
            'order': 1,
            'subscale': 0,
            'text': 'Test Question',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['labels'], ['family', 'health'])


class TestOpenEndedQuestionForm(TestCase):

    def test_unbound(self):
        form = OpenEndedQuestionForm()
        expected_fields = [
            'available', 'input_type', 'instructions', 'instruments', 'labels',
            'order', 'subscale', 'text',
        ]
        self.assertEqual(
            sorted(list(form.fields.keys())),
            expected_fields
        )

    def test_bound(self):
        form = OpenEndedQuestionForm({
            'available': True,
            'input_type': 'text',
            'instructions': 'To do',
            'instruments': '',
            'labels': 'family,health',
            'order': 1,
            'subscale': 0,
            'text': 'Test Question',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['labels'], ['family', 'health'])
