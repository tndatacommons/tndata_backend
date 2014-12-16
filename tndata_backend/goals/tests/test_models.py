from datetime import datetime, time, timezone

from django.test import TestCase
from django.contrib.auth import get_user_model

from .. models import (
    Behavior, BehaviorStep, ChosenBehavior, CompletedBehaviorStep,
    CustomReminder, Goal
)


class TestGoal(TestCase):
    """Tests for the `Goal` model."""

    def setUp(self):
        self.goal = Goal.objects.create(
            rank=1,
            name='Test Goal',
            explanation='Some explanation!',
            max_neef_tags=['subsistence', 'protection', 'affection'],
            sdt_major='Autonomy'
        )

    def tearDown(self):
        Goal.objects.filter(id=self.goal.id).delete()

    def test__str__(self):
        expected = "Test Goal"
        actual = "{}".format(self.goal)
        self.assertEqual(expected, actual)


class TestBehavior(TestCase):
    """Tests for the `Behavior` model."""

    def setUp(self):
        self.goal = Goal.objects.create(
            rank=1,
            name='Test Goal',
            explanation='Some explanation!',
            max_neef_tags=['subsistence', 'protection', 'affection'],
            sdt_major='Autonomy'
        )
        self.behavior = Behavior.objects.create(
            goal=self.goal,
            name='Test Behavior',
            summary='This is a behavior!',
            description='Heres a description'
        )

    def tearDown(self):
        Goal.objects.filter(id=self.goal.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()

    def test__str__(self):
        expected = "Test Behavior"
        actual = "{}".format(self.behavior)
        self.assertEqual(expected, actual)


class TestBehaviorStep(TestCase):
    """Tests for the `BehaviorStep` model."""

    def setUp(self):
        self.goal = Goal.objects.create(
            rank=1,
            name='Test Goal',
            explanation='Some explanation!',
            max_neef_tags=['subsistence', 'protection', 'affection'],
            sdt_major='Autonomy'
        )
        self.behavior = Behavior.objects.create(
            goal=self.goal,
            name='Test Behavior',
            summary='This is a behavior!',
            description='Heres a description'
        )
        self.behavior_step = BehaviorStep.objects.create(
            goal=self.goal,
            behavior=self.behavior,
            name='Test Behavior Step',
            description='This is a behavior step description',
            reminder_type='temporal',
        )
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="x"
        )

    def tearDown(self):
        Goal.objects.filter(id=self.goal.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()
        BehaviorStep.objects.filter(id=self.behavior.id).delete()
        self.User.objects.filter(id=self.user.id).delete()

    def test__str__(self):
        expected = "Test Behavior Step"
        actual = "{}".format(self.behavior_step)
        self.assertEqual(expected, actual)

    def test_reminder(self):
        # No custom reminder, so this should return the default (which is blank)
        self.assertEqual(
            self.behavior_step.reminder(self.user),
            ('temporal', None, '', '')
        )

    def test_get_custom_reminder(self):
        # No custom reminder, so should be None
        self.assertIsNone(self.behavior_step.get_custom_reminder(self.user))


class TestCustomReminder(TestCase):
    """Tests for the `CustomReminder` model."""

    def setUp(self):
        self.goal = Goal.objects.create(
            rank=1,
            name='Test Goal',
            explanation='Some explanation!',
            max_neef_tags=['subsistence', 'protection', 'affection'],
            sdt_major='Autonomy'
        )
        self.behavior = Behavior.objects.create(
            goal=self.goal,
            name='Test Behavior',
            summary='This is a behavior!',
            description='Heres a description'
        )
        self.behavior_step = BehaviorStep.objects.create(
            goal=self.goal,
            behavior=self.behavior,
            name='Test Behavior Step',
            description='This is a behavior step description',
            reminder_type='temporal',
            default_repeat='daily',
        )
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="x"
        )
        self.reminder = CustomReminder.objects.create(
            user=self.user,
            behavior_step=self.behavior_step,
            reminder_type="daily",
            #time=time(13, 30, 45, tzinfo=timezone.utc),
            time=datetime.utcnow(),
            repeat="daily",
            location=''
        )

    def tearDown(self):
        Goal.objects.filter(id=self.goal.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()
        BehaviorStep.objects.filter(id=self.behavior.id).delete()
        self.User.objects.filter(id=self.user.id).delete()
        CustomReminder.objects.filter(id=self.reminder.id).delete()

    def test__str__(self):
        expected = "Custom Reminder for Test Behavior Step"
        actual = "{0}".format(self.reminder)
        self.assertEqual(expected, actual)


class TestChosenBehavior(TestCase):
    """Tests for the `ChosenBehavior` model."""

    def setUp(self):
        self.goal = Goal.objects.create(
            rank=1,
            name='Test Goal',
            explanation='Some explanation!',
            max_neef_tags=['subsistence', 'protection', 'affection'],
            sdt_major='Autonomy'
        )
        self.behavior = Behavior.objects.create(
            goal=self.goal,
            name='Test Behavior',
            summary='This is a behavior!',
            description='Heres a description'
        )
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="x"
        )
        self.chosen_behavior = ChosenBehavior.objects.create(
            user=self.user,
            goal=self.goal,
            behavior=self.behavior,
        )

    def tearDown(self):
        Goal.objects.filter(id=self.goal.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()
        self.User.objects.filter(id=self.user.id).delete()
        ChosenBehavior.objects.filter(id=self.chosen_behavior.id).delete()

    def test__str__(self):
        expected = "Test Behavior selected on {0}".format(self.chosen_behavior.date_selected)
        actual = "{}".format(self.chosen_behavior)
        self.assertEqual(expected, actual)


class TestCompletedBehaviorStep(TestCase):
    """Tests for the `CompletedBehaviorStep` model."""

    def setUp(self):
        self.goal = Goal.objects.create(
            rank=1,
            name='Test Goal',
            explanation='Some explanation!',
            max_neef_tags=['subsistence', 'protection', 'affection'],
            sdt_major='Autonomy'
        )
        self.behavior = Behavior.objects.create(
            goal=self.goal,
            name='Test Behavior',
            summary='This is a behavior!',
            description='Heres a description'
        )
        self.behavior_step = BehaviorStep.objects.create(
            goal=self.goal,
            behavior=self.behavior,
            name='Test Behavior Step',
            description='This is a behavior step description',
            reminder_type='temporal',
            default_repeat='daily',
        )
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="x"
        )
        self.completed_step = CompletedBehaviorStep.objects.create(
            user=self.user,
            goal=self.goal,
            behavior=self.behavior,
            behavior_step=self.behavior_step
        )

    def tearDown(self):
        Goal.objects.filter(id=self.goal.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()
        BehaviorStep.objects.filter(id=self.behavior_step.id).delete()
        self.User.objects.filter(id=self.user.id).delete()
        CompletedBehaviorStep.objects.filter(id=self.completed_step.id).delete()

    def test__str__(self):
        expected = "Test Behavior Step completed on {0}".format(
            self.completed_step.date_completed
        )
        actual = "{}".format(self.completed_step)
        self.assertEqual(expected, actual)
