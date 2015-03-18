from django.contrib.auth import get_user_model
from django.test import TestCase

from .. models import (
    LikertQuestion,
    LikertResponse,
    MultipleChoiceQuestion,
    MultipleChoiceResponse,
    MultipleChoiceResponseOption,
    OpenEndedQuestion,
    OpenEndedResponse,
)


class TestLikertQuestion(TestCase):
    """Tests for the `LikertQuestion` model."""

    def setUp(self):
        self.question = LikertQuestion.objects.create(
            text="What is your favorite color?"
        )

    def tearDown(self):
        LikertQuestion.objects.filter(id=self.question.id).delete()

    def test__str__(self):
        expected = "What is your favorite color?"
        actual = "{}".format(self.question)
        self.assertEqual(expected, actual)

    def test_options(self):
        expected_options = [
            {"id": 1, "text": "Strongly Disagree"},
            {"id": 2, "text": "Disagree"},
            {"id": 3, "text": "Slightly Disagree"},
            {"id": 4, "text": "Neither Agree nor Disagree"},
            {"id": 5, "text": "Slightly Agree"},
            {"id": 6, "text": "Agree"},
            {"id": 7, "text": "Strongly Agree"},
        ]
        self.assertEqual(self.question.options, expected_options)

    def test_get_absolute_url(self):
        self.assertEqual(
            self.question.get_absolute_url(),
            "/survey/likert/{0}/".format(self.question.id)
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.question.get_update_url(),
            "/survey/likert/{0}/update/".format(self.question.id)
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.question.get_delete_url(),
            "/survey/likert/{0}/delete/".format(self.question.id)
        )


class TestLikertResponse(TestCase):
    """Tests for the `LikertResponse` model."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "user", "user@example.com", "secret"
        )
        self.question = LikertQuestion.objects.create(
            text="What is your favorite color?"
        )
        self.response = LikertResponse.objects.create(
            user=self.user,
            question=self.question,
            selected_option=LikertQuestion.STRONGLY_DISAGREE,
        )

    def tearDown(self):
        get_user_model().objects.filter(username="user").delete()
        LikertQuestion.objects.filter(id=self.question.id).delete()
        LikertResponse.objects.filter(id=self.response.id).delete()

    def test__str__(self):
        expected = "Strongly Disagree"
        actual = "{}".format(self.response)
        self.assertEqual(expected, actual)


class TestOpenEndedQuestion(TestCase):
    """Tests for the `OpenEndedQuestion` model."""

    def setUp(self):
        self.question = OpenEndedQuestion.objects.create(
            text="What is your favorite color?"
        )

    def tearDown(self):
        OpenEndedQuestion.objects.filter(id=self.question.id).delete()

    def test__str__(self):
        expected = "What is your favorite color?"
        actual = "{}".format(self.question)
        self.assertEqual(expected, actual)

    def test_get_absolute_url(self):
        self.assertEqual(
            self.question.get_absolute_url(),
            "/survey/openended/{0}/".format(self.question.id)
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.question.get_update_url(),
            "/survey/openended/{0}/update/".format(self.question.id)
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.question.get_delete_url(),
            "/survey/openended/{0}/delete/".format(self.question.id)
        )


class TestOpenEndedResponse(TestCase):
    """Tests for the `OpenEndedResponse` model."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "user", "user@example.com", "secret"
        )
        self.question = OpenEndedQuestion.objects.create(
            text="What is your favorite color?"
        )
        self.response = OpenEndedResponse.objects.create(
            user=self.user,
            question=self.question,
            response="Yellow. No Blue!"
        )

    def tearDown(self):
        get_user_model().objects.filter(username="user").delete()
        OpenEndedQuestion.objects.filter(id=self.question.id).delete()
        OpenEndedResponse.objects.filter(id=self.response.id).delete()

    def test__str__(self):
        expected = "Yellow. No Blue!"
        actual = "{}".format(self.response)
        self.assertEqual(expected, actual)


class TestMultipleChoiceQuestion(TestCase):
    """Tests for the `MultipleChoiceQuestion` model."""

    def setUp(self):
        self.question = MultipleChoiceQuestion.objects.create(
            text="What is your favorite color?"
        )

    def tearDown(self):
        MultipleChoiceQuestion.objects.filter(id=self.question.id).delete()

    def test__str__(self):
        expected = "What is your favorite color?"
        actual = "{}".format(self.question)
        self.assertEqual(expected, actual)

    def test_options_when_empty(self):
        # When there are no options.
        self.assertEqual(self.question.options, [])

    def test_options(self):
        # Define some options for this question.
        a = MultipleChoiceResponseOption.objects.create(
            question=self.question,
            text='A'
        )
        b = MultipleChoiceResponseOption.objects.create(
            question=self.question,
            text='B'
        )

        expected = [
            {"id": a.id, "text": "A"},
            {"id": b.id, "text": "B"},
        ]
        self.assertEqual(self.question.options, expected)

        # Clean Up
        a.delete()
        b.delete()

    def test_get_absolute_url(self):
        self.assertEqual(
            self.question.get_absolute_url(),
            "/survey/multiplechoice/{0}/".format(self.question.id)
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.question.get_update_url(),
            "/survey/multiplechoice/{0}/update/".format(self.question.id)
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.question.get_delete_url(),
            "/survey/multiplechoice/{0}/delete/".format(self.question.id)
        )


class TestMultipleChoiceResponseOption(TestCase):
    """Tests for the `MultipleChoiceResponseOption` model."""

    def setUp(self):
        self.question = MultipleChoiceQuestion.objects.create(
            text="What is your favorite color?"
        )
        self.option = MultipleChoiceResponseOption.objects.create(
            question=self.question,
            text="Blue?"
        )

    def tearDown(self):
        MultipleChoiceQuestion.objects.filter(id=self.question.id).delete()
        MultipleChoiceResponseOption.objects.filter(id=self.option.id).delete()

    def test__str__(self):
        expected = "Blue?"
        actual = "{}".format(self.option)
        self.assertEqual(expected, actual)


class TestMultipleChoiceResponse(TestCase):
    """Tests for the `MultipleChoiceResponse` model."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "user", "user@example.com", "secret"
        )
        self.question = MultipleChoiceQuestion.objects.create(
            text="What is your favorite color?"
        )
        self.option = MultipleChoiceResponseOption.objects.create(
            question=self.question,
            text="Blue?"
        )
        self.response = MultipleChoiceResponse.objects.create(
            user=self.user,
            question=self.question,
            selected_option=self.option,
        )

    def tearDown(self):
        get_user_model().objects.filter(username="user").delete()
        MultipleChoiceQuestion.objects.filter(id=self.question.id).delete()
        MultipleChoiceResponseOption.objects.filter(id=self.option.id).delete()
        MultipleChoiceResponse.objects.filter(id=self.response.id).delete()

    def test__str__(self):
        expected = "Blue?"
        actual = "{}".format(self.option)
        self.assertEqual(expected, actual)
