from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase

from .. likert import LIKERT_SCALES
from .. models import (
    Instrument,
    BinaryQuestion,
    BinaryResponse,
    LikertQuestion,
    LikertResponse,
    MultipleChoiceQuestion,
    MultipleChoiceResponse,
    MultipleChoiceResponseOption,
    OpenEndedQuestion,
    OpenEndedResponse,
)


class TestInstrument(TestCase):
    """Tests for the `Instrument` model."""

    def setUp(self):
        self.instrument = Instrument.objects.create(
            title="Test Instrument"
        )

    def tearDown(self):
        Instrument.objects.filter(id=self.instrument.id).delete()

    def test__str__(self):
        expected = "Test Instrument"
        actual = "{}".format(self.instrument)
        self.assertEqual(expected, actual)

    def test_questions(self):
        q1 = BinaryQuestion.objects.create(text="Q1")
        q2 = LikertQuestion.objects.create(text="Q2")
        q3 = OpenEndedQuestion.objects.create(text="Q3")
        q4 = MultipleChoiceQuestion.objects.create(text="Q4")
        for q in [q1, q2, q3, q4]:
            q.instruments.add(self.instrument)

        expected = [
            ('BinaryQuestion', q1),
            ('LikertQuestion', q2),
            ('OpenEndedQuestion', q3),
            ('MultipleChoiceQuestion', q4)
        ]
        self.assertEqual(self.instrument.questions, expected)

        # Clean up.
        q1.delete()
        q2.delete()
        q3.delete()
        q4.delete()

    def test_get_absolute_url(self):
        self.assertEqual(
            self.instrument.get_absolute_url(),
            "/survey/instrument/{0}/".format(self.instrument.id)
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.instrument.get_update_url(),
            "/survey/instrument/{0}/update/".format(self.instrument.id)
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.instrument.get_delete_url(),
            "/survey/instrument/{0}/delete/".format(self.instrument.id)
        )


class TestBaseQuestion(TestCase):
    """Test any methods on BaseQuestion that are not Question-specific."""

    def test_get_instructions_from_instrument(self):
        """ensure that a question can return instructions from the instrument."""
        i = Instrument.objects.create(title="X", instructions="Testing")
        q = BinaryQuestion.objects.create(text="Q")
        q.instruments.add(i)
        self.assertEqual(q.get_instructions(), "Testing")
        i.delete()
        q.delete()

    def test_get_instructions_from_question(self):
        """Ensure that a question can returns it's own instructions if they exist."""
        i = Instrument.objects.create(title="X", instructions="Testing")
        q = BinaryQuestion.objects.create(text="Q", instructions="Get These")
        q.instruments.add(i)
        self.assertEqual(q.get_instructions(), "Get These")
        i.delete()
        q.delete()


class TestBinaryQuestion(TestCase):
    """Tests for the `BinaryQuestion` model."""

    def setUp(self):
        self.question = BinaryQuestion.objects.create(
            text="Is this a yes or no question?"
        )

    def tearDown(self):
        BinaryQuestion.objects.filter(id=self.question.id).delete()

    def test__str__(self):
        expected = "Is this a yes or no question?"
        actual = "{}".format(self.question)
        self.assertEqual(expected, actual)

    def test_question_type(self):
        self.assertEqual(self.question.question_type, "binaryquestion")

    def test_options(self):
        expected_options = [
            {"id": False, "text": "No"},
            {"id": True, "text": "Yes"},
        ]
        self.assertEqual(self.question.options, expected_options)

    def test_get_absolute_url(self):
        self.assertEqual(
            self.question.get_absolute_url(),
            "/survey/binary/{0}/".format(self.question.id)
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.question.get_update_url(),
            "/survey/binary/{0}/update/".format(self.question.id)
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.question.get_delete_url(),
            "/survey/binary/{0}/delete/".format(self.question.id)
        )

    def test_get_api_response_url(self):
        self.assertEqual(
            self.question.get_api_response_url(),
            "/api/survey/binary/responses/".format(self.question.id)
        )


class TestBinaryResponse(TestCase):
    """Tests for the `BinaryResponse` model."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "user", "user@example.com", "secret"
        )
        self.question = BinaryQuestion.objects.create(
            text="Is this a yes or no question?"
        )
        self.response = BinaryResponse.objects.create(
            user=self.user,
            question=self.question,
            selected_option=True,
        )

    def tearDown(self):
        get_user_model().objects.filter(username="user").delete()
        BinaryQuestion.objects.filter(id=self.question.id).delete()
        BinaryResponse.objects.filter(id=self.response.id).delete()

    def test__str__(self):
        self.assertEqual("{}".format(self.response), "Yes")


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

    def test_question_type(self):
        self.assertEqual(self.question.question_type, "likertquestion")

    def test_options(self):
        expected_options = [
            {"id": d[0], "text": d[1]} for d in LIKERT_SCALES['5_point_agreement']
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
            text="What is your favorite color?",
            scale="5_point_agreement"
        )
        self.response = LikertResponse.objects.create(
            user=self.user,
            question=self.question,
            selected_option=LIKERT_SCALES['5_point_agreement'][0][0]
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

    def test_question_type(self):
        self.assertEqual(self.question.question_type, "openendedquestion")

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

    def test_convert_to_input_type(self):
        """Ensure the `convert_to_input_type` returns the correct type of data."""
        self.question.input_type = "text"
        self.question.save()
        self.assertEqual(self.question.convert_to_input_type("foo"), "foo")

        self.question.input_type = "numeric"
        self.question.save()
        self.assertEqual(self.question.convert_to_input_type("42"), 42)

        self.question.input_type = "datetime"
        self.question.save()
        self.assertEqual(
            self.question.convert_to_input_type("2015-04-20"),
            datetime(2015, 4, 20)
        )

        self.question.input_type = "datetime"
        self.question.save()
        self.assertEqual(
            self.question.convert_to_input_type("2015-04-20 12:32:45"),
            datetime(2015, 4, 20, 12, 32, 45)
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

    def test_response_as_input_type(self):
        """Ensure this method returns a data type specified by the question's
        input_type field."""
        kwargs = {'user': self.user, 'question': None, 'response': None}

        q = OpenEndedQuestion.objects.create(text="A", input_type="text")
        kwargs['question'] = q
        kwargs['response'] = "hi"
        r = OpenEndedResponse.objects.create(**kwargs)
        self.assertEqual(type(r.get_response_as_input_type()), str)
        self.assertEqual(r.get_response_as_input_type(), "hi")
        q.delete()
        r.delete()

        q = OpenEndedQuestion.objects.create(text="B", input_type="numeric")
        kwargs['question'] = q
        kwargs['response'] = "7"
        r = OpenEndedResponse.objects.create(**kwargs)
        self.assertEqual(type(r.get_response_as_input_type()), int)
        self.assertEqual(r.get_response_as_input_type(), 7)
        q.delete()
        r.delete()

        q = OpenEndedQuestion.objects.create(text="C", input_type="datetime")
        kwargs['question'] = q
        kwargs['response'] = "04-20-2015"
        r = OpenEndedResponse.objects.create(**kwargs)
        self.assertEqual(type(r.get_response_as_input_type()), datetime)
        self.assertEqual(r.get_response_as_input_type(), datetime(2015, 4, 20))
        q.delete()
        r.delete()

        q = OpenEndedQuestion.objects.create(text="D", input_type="datetime")
        kwargs['question'] = q
        kwargs['response'] = "04-20-2015 13:40:56"
        r = OpenEndedResponse.objects.create(**kwargs)
        self.assertEqual(type(r.get_response_as_input_type()), datetime)
        self.assertEqual(
            r.get_response_as_input_type(),
            datetime(2015, 4, 20, 13, 40, 56)
        )
        q.delete()
        r.delete()


class TestMultipleChoiceQuestion(TestCase):
    """Tests for the `MultipleChoiceQuestion` model."""

    def setUp(self):
        self.question = MultipleChoiceQuestion.objects.create(
            text="What is your favorite color?"
        )

    def tearDown(self):
        MultipleChoiceQuestion.objects.filter(id=self.question.id).delete()

    def test_question_type(self):
        self.assertEqual(self.question.question_type, "multiplechoicequestion")

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
