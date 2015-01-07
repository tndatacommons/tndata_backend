from datetime import datetime, time

from django.test import TestCase
from django.contrib.auth import get_user_model

from .. models import (
    Action,
    ActionTaken,
    Category,
    Interest,
    CustomReminder,
    SelectedAction,
)


class TestCategory(TestCase):
    """Tests for the `Category` model."""

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            name='Test Category',
            description='Some explanation!',
        )

    def tearDown(self):
        Category.objects.filter(id=self.category.id).delete()

    def test__str__(self):
        expected = "Test Category"
        actual = "{}".format(self.category)
        self.assertEqual(expected, actual)


class TestInterest(TestCase):
    """Tests for the `Interest` model."""

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            name='Test Category',
            description='Category Description',
        )
        self.interest = Interest.objects.create(
            order=1,
            name='Test Interest',
            description='Heres a description',
            max_neef_tags=['subsistence', 'protection', 'affection'],
        )
        self.interest.categories.add(self.category)

    def tearDown(self):
        Category.objects.filter(id=self.category.id).delete()
        Interest.objects.filter(id=self.interest.id).delete()

    def test__str__(self):
        expected = "Test Interest"
        actual = "{}".format(self.interest)
        self.assertEqual(expected, actual)


class TestAction(TestCase):
    """Tests for the `Action` model."""

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            name='Test Category',
            description='Some explanation!',
        )
        self.interest = Interest.objects.create(
            order=1,
            name='Test Interest',
            description='Heres a description',
            max_neef_tags=['subsistence', 'protection', 'affection'],
        )
        self.interest.categories.add(self.category)

        self.action = Action.objects.create(
            order=1,
            name='Test Action',
            summary="Testing an Action",
            description='This is a action description',
            # NOTE: Omitting the default reminder time/frequency.
        )
        self.action.interests.add(self.interest)

        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="x"
        )

    def tearDown(self):
        Action.objects.filter(id=self.interest.id).delete()
        Interest.objects.filter(id=self.interest.id).delete()
        Category.objects.filter(id=self.category.id).delete()
        self.User.objects.filter(id=self.user.id).delete()

    def test__str__(self):
        expected = "Test Action"
        actual = "{}".format(self.action)
        self.assertEqual(expected, actual)

    def test_reminder(self):
        # No custom reminder, so this should return the default (which is blank)
        self.assertEqual(self.action.reminder(self.user), (None, ''))

    def test_get_custom_reminder(self):
        # No custom reminder, so should be None
        self.assertIsNone(self.action.get_custom_reminder(self.user))


class TestCustomReminder(TestCase):
    """Tests for the `CustomReminder` model."""

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            name='Test Category',
            description='Some explanation!',
        )
        self.interest = Interest.objects.create(
            order=1,
            name='Test Interest',
            description='Heres a description',
            max_neef_tags=['subsistence', 'protection', 'affection'],
        )
        self.interest.categories.add(self.category)

        self.action = Action.objects.create(
            order=1,
            name='Test Action',
            summary="Testing an Action",
            description='This is a action description',
            default_reminder_time=time(13, 30),
            default_reminder_frequency="daily"
        )
        self.action.interests.add(self.interest)

        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="x"
        )
        self.reminder = CustomReminder.objects.create(
            user=self.user,
            action=self.action,
            frequency="daily",
            time=datetime.utcnow(),
        )

    def tearDown(self):
        Category.objects.filter(id=self.category.id).delete()
        Interest.objects.filter(id=self.interest.id).delete()
        Action.objects.filter(id=self.interest.id).delete()
        self.User.objects.filter(id=self.user.id).delete()
        CustomReminder.objects.filter(id=self.reminder.id).delete()

    def test__str__(self):
        expected = "Custom Reminder for Test Action"
        actual = "{0}".format(self.reminder)
        self.assertEqual(expected, actual)


class TestSelectedAction(TestCase):
    """Tests for the `SelectedAction` model."""

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            name='Test Category',
            description='Some explanation!',
        )
        self.interest = Interest.objects.create(
            order=1,
            name='Test Interest',
            description='Heres a description',
            max_neef_tags=['subsistence', 'protection', 'affection'],
        )
        self.interest.categories.add(self.category)

        self.action = Action.objects.create(
            order=1,
            name='Test Action',
            summary="Testing an Action",
            description='This is a action description',
            default_reminder_time=time(13, 30),
            default_reminder_frequency="daily"
        )
        self.action.interests.add(self.interest)

        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="x"
        )
        self.selected_action = SelectedAction.objects.create(
            user=self.user,
            action=self.action
        )

    def tearDown(self):
        Category.objects.filter(id=self.category.id).delete()
        Interest.objects.filter(id=self.interest.id).delete()
        Action.objects.filter(id=self.action.id).delete()

        self.User.objects.filter(id=self.user.id).delete()
        SelectedAction.objects.filter(id=self.selected_action.id).delete()

    def test__str__(self):
        date_selected = self.selected_action.date_selected
        expected = "Test Action selected on {0}".format(date_selected)
        actual = "{}".format(self.selected_action)
        self.assertEqual(expected, actual)

    def test_name(self):
        self.assertEqual(self.action.name, self.selected_action.name)


class TestActionTaken(TestCase):
    """Tests for the `ActionTaken` model."""

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            name='Test Category',
            description='Some explanation!',
        )
        self.interest = Interest.objects.create(
            order=1,
            name='Test Interest',
            description='Heres a description',
            max_neef_tags=['subsistence', 'protection', 'affection'],
        )
        self.interest.categories.add(self.category)

        self.action = Action.objects.create(
            order=1,
            name='Test Action',
            summary="Testing an Action",
            description='This is a action description',
            default_reminder_time=time(13, 30),
            default_reminder_frequency="daily"
        )
        self.action.interests.add(self.interest)

        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="x"
        )

        self.selected_action = SelectedAction.objects.create(
            user=self.user,
            action=self.action
        )
        self.action_taken = ActionTaken.objects.create(
            user=self.user,
            selected_action=self.selected_action
        )

    def tearDown(self):
        Category.objects.filter(id=self.category.id).delete()
        Interest.objects.filter(id=self.interest.id).delete()
        Action.objects.filter(id=self.action.id).delete()
        SelectedAction.objects.filter(id=self.selected_action.id).delete()
        ActionTaken.objects.filter(id=self.action_taken.id).delete()
        self.User.objects.filter(id=self.user.id).delete()

    def test__str__(self):
        expected = "Test Action completed on {0}".format(
            self.action_taken.date_completed
        )
        actual = "{}".format(self.action_taken)
        self.assertEqual(expected, actual)
