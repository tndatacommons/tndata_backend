from django.contrib.auth import get_user_model
from django.test import TestCase

from goals.models import Category  # For the labels.

from .. models import (
    Instrument,
    BinaryQuestion,
    LikertQuestion,
    LikertResponse,
    SurveyResult,
)
User = get_user_model()


class TestSurveyResultManager(TestCase):

    def setUp(self):
        # We need Categories for labels.
        Category.objects.create(order=1, title="Family")
        Category.objects.create(order=2, title="Happiness")
        Category.objects.create(order=3, title="Wellness")

        # We need an instrument, and a number of questions + some responses
        # in order to accurately test this.
        self.instrument = Instrument.objects.create(title="Test Instrument")
        self.user = User.objects.create(username="t", email="t@example.com")

        # Create the likert questions for this instrument.
        self.q1 = LikertQuestion.objects.create(
            text="Q1",
            subscale=1,  # Importance
            order=1,
            scale="5_point_necessary",
            labels=['family', 'happiness']
        )
        self.q2 = LikertQuestion.objects.create(
            text="Q2",
            subscale=1,  # Importance
            order=2,
            scale="5_point_necessary",
            labels=['wellness']
        )
        self.q3 = LikertQuestion.objects.create(
            text="Q3",
            subscale=2,  # Satisfaction
            order=3,
            scale="5_point_satisfaction",
            labels=['family', 'happiness']
        )
        self.q4 = LikertQuestion.objects.create(
            text="Q4",
            subscale=2,  # Satisfaction
            order=4,
            scale="5_point_satisfaction",
            labels=['wellness']
        )
        for q in LikertQuestion.objects.filter(text__startswith='Q'):
            q.instruments.add(self.instrument)

    def tearDown(self):
        for model in [Category, Instrument, LikertQuestion, LikertResponse, User]:
            model.objects.all().delete()

    def test_question_ordering(self):
        """Questions must get ordered by Subscale / order."""
        self.assertEqual(
            list(LikertQuestion.objects.values_list("text", flat=True)),
            ["Q1", "Q2", "Q3", "Q4"]
        )

    def test_create_objects(self):
        """Test ideal conditions."""
        # Create some responses for the user.
        LikertResponse.objects.create(
            user=self.user,
            question=self.q1,
            selected_option=1  # Very Unnecessary
        )
        LikertResponse.objects.create(
            user=self.user,
            question=self.q2,
            selected_option=5  # Very Necessary
        )
        LikertResponse.objects.create(
            user=self.user,
            question=self.q3,
            selected_option=5  # Very Satisfied
        )
        LikertResponse.objects.create(
            user=self.user,
            question=self.q4,
            selected_option=1  # Very Dissatisfied
        )
        results = SurveyResult.objects.create_objects(self.user, self.instrument)
        self.assertEqual(results.count(), 2)

        # Scores should be:
        # -------------------
        # q1 - q3: 1 - 5 = 0
        # q2 - q4: 5 - 1 = 4
        # -------------------

        # Verify the result that should contain score=0
        qs = SurveyResult.objects.filter(
            user=self.user, instrument=self.instrument, score=0
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(  # Should have the labels from q1 & q3
            sorted(qs.values_list('labels', flat=True)[0]),
            sorted(['family', 'happiness'])
        )

        # Verify the result that should contain score=4
        qs = SurveyResult.objects.filter(
            user=self.user, instrument=self.instrument, score=4
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(  # Should have the labels from q2 & q4
            sorted(qs.values_list('labels', flat=True)[0]),
            sorted(['wellness'])
        )

    def test_create_objects_when_no_responses(self):
        """Should return no results when there are no responses."""
        results = SurveyResult.objects.create_objects(self.user, self.instrument)
        self.assertEqual(results.count(), 0)

    def test_create_objects_fails_when_not_all_likert(self):
        """Any non-likert questions in the instrument should raise an exception"""
        q = BinaryQuestion.objects.create(text="Q1")
        q.instruments.add(self.instrument)
        q.save()
        with self.assertRaises(ValueError):
            SurveyResult.objects.create_objects(self.user, self.instrument)

        # Clean up
        q.delete()

    def test_create_objects_fails_when_wrong_number_of_questions(self):
        """An odd number of questions in the instrument should raise an exception"""
        # Adding an odd-number of questions to the instrument.
        q = LikertQuestion.objects.create(text="Q5")
        q.instruments.add(self.instrument)
        q.save()
        with self.assertRaises(ValueError):
            SurveyResult.objects.create_objects(self.user, self.instrument)
        # Clean up
        q.delete()
