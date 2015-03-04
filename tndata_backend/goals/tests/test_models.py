from datetime import datetime, time

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from .. models import (
    Action,
    ActionTaken,
    Category,
    Goal,
    Trigger,
    BehaviorSequence,
    BehaviorAction,
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

    def test_save(self):
        """Verify that saving generates a name_slug"""
        category = Category.objects.create(order=2, name="New Name")
        category.save()
        self.assertEqual(category.name_slug, "new-name")

    def test_goals(self):
        self.assertIsInstance(self.category.goals, QuerySet)

    def test_get_absolute_url(self):
        self.assertEqual(
            self.category.get_absolute_url(),
            "/goals/category/test-category/"
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.category.get_update_url(),
            "/goals/category/test-category/update/"
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.category.get_delete_url(),
            "/goals/category/test-category/delete/"
        )


class TestGoal(TestCase):
    """Tests for the `Goal` model."""

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            name='Test Category',
            description='Category Description',
        )
        self.goal = Goal.objects.create(
            name="Test Goal",
            title="Title for Test Goal",
            description="A Description",
            outcome="An Outcome"
        )
        self.goal.categories.add(self.category)

    def tearDown(self):
        Goal.objects.filter(id=self.goal.id).delete()
        Category.objects.filter(id=self.category.id).delete()

    def test__str__(self):
        expected = "Test Goal"
        actual = "{}".format(self.goal)
        self.assertEqual(expected, actual)

    def test_save(self):
        """Verify that saving generates a name_slug"""
        goal = Goal.objects.create(name="New Name")
        goal.save()
        self.assertEqual(goal.name_slug, "new-name")

    def test_get_absolute_url(self):
        self.assertEqual(
            self.goal.get_absolute_url(),
            "/goals/goal/test-goal/"
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.goal.get_update_url(),
            "/goals/goal/test-goal/update/"
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.goal.get_delete_url(),
            "/goals/goal/test-goal/delete/"
        )


class TestTrigger(TestCase):
    """Tests for the `Trigger` model."""

    def setUp(self):
        self.trigger = Trigger.objects.create(
            name="Test Trigger",
            trigger_type="time",
            frequency="one-time",
            time="13:30",
            date="2014-02-01",
            text="Testing",
            instruction="Help"
        )

    def tearDown(self):
        Trigger.objects.filter(id=self.trigger.id).delete()

    def test__str__(self):
        expected = "Test Trigger"
        actual = "{}".format(self.trigger)
        self.assertEqual(expected, actual)

    def test_save(self):
        """Verify that saving generates a name_slug"""
        trigger = Trigger.objects.create(
            name="New Name",
            trigger_type="time",
            frequency="one-time"
        )
        trigger.save()
        self.assertEqual(trigger.name_slug, "new-name")

    def test_get_absolute_url(self):
        self.assertEqual(
            self.trigger.get_absolute_url(),
            "/goals/trigger/test-trigger/"
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.trigger.get_update_url(),
            "/goals/trigger/test-trigger/update/"
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.trigger.get_delete_url(),
            "/goals/trigger/test-trigger/delete/"
        )


class TestBehaviorSequence(TestCase):
    """Tests for the `BehaviorSequence` model."""

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            name='Test Category',
            description='Category Description',
        )
        self.goal = Goal.objects.create(name="Test Goal")
        self.bs = BehaviorSequence.objects.create(
            name='Test BehaviorSequence',
            title="Formal Title",
        )
        self.bs.categories.add(self.category)
        self.bs.goals.add(self.goal)

    def tearDown(self):
        Category.objects.filter(id=self.category.id).delete()
        Goal.objects.filter(id=self.goal.id).delete()
        BehaviorSequence.objects.filter(id=self.bs.id).delete()

    def test__str__(self):
        expected = "Test BehaviorSequence"
        actual = "{}".format(self.bs)
        self.assertEqual(expected, actual)

    def test_save(self):
        """Verify that saving generates a name_slug"""
        bs = BehaviorSequence.objects.create(name="New Name", title="X")
        bs.save()
        self.assertEqual(bs.name_slug, "new-name")

    def test_get_absolute_url(self):
        self.assertEqual(
            self.bs.get_absolute_url(),
            "/goals/behaviorsequence/test-behaviorsequence/"
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.bs.get_update_url(),
            "/goals/behaviorsequence/test-behaviorsequence/update/"
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.bs.get_delete_url(),
            "/goals/behaviorsequence/test-behaviorsequence/delete/"
        )


class TestBehaviorAction(TestCase):
    """Tests for the `BehaviorAction` model."""

    def setUp(self):
        self.bs = BehaviorSequence.objects.create(
            name='Test BehaviorSequence',
            title="Formal Title",
        )
        self.ba = BehaviorAction.objects.create(
            sequence=self.bs,
            name="Test BehaviorAction",
            title="Formal Action Title",
        )

    def tearDown(self):
        BehaviorSequence.objects.filter(id=self.bs.id).delete()
        BehaviorAction.objects.filter(id=self.ba.id).delete()

    def test__str__(self):
        expected = "Test BehaviorAction"
        actual = "{}".format(self.ba)
        self.assertEqual(expected, actual)

    def test_save(self):
        """Verify that saving generates a name_slug"""
        ba = BehaviorAction.objects.create(
            sequence=self.bs, name="New Name", title="X"
        )
        ba.save()
        self.assertEqual(ba.name_slug, "new-name")

    def test_get_absolute_url(self):
        self.assertEqual(
            self.ba.get_absolute_url(),
            "/goals/behavioraction/test-behavioraction/"
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.ba.get_update_url(),
            "/goals/behavioraction/test-behavioraction/update/"
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.ba.get_delete_url(),
            "/goals/behavioraction/test-behavioraction/delete/"
        )


class TestAction(TestCase):
    """Tests for the `Action` model."""

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            name='Test Category',
            description='Some explanation!',
        )
        self.action = Action.objects.create(
            order=1,
            name='Test Action',
            summary="Testing an Action",
            description='This is a action description',
            # NOTE: Omitting the default reminder time/frequency.
        )
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="x"
        )

    def tearDown(self):
        Action.objects.filter(id=self.action.id).delete()
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
        self.action = Action.objects.create(
            order=1,
            name='Test Action',
            summary="Testing an Action",
            description='This is a action description',
            default_reminder_time=time(13, 30),
            default_reminder_frequency="daily"
        )

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
        Action.objects.filter(id=self.action.id).delete()
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
        self.action = Action.objects.create(
            order=1,
            name='Test Action',
            summary="Testing an Action",
            description='This is a action description',
            default_reminder_time=time(13, 30),
            default_reminder_frequency="daily"
        )

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
        self.action = Action.objects.create(
            order=1,
            name='Test Action',
            summary="Testing an Action",
            description='This is a action description',
            default_reminder_time=time(13, 30),
            default_reminder_frequency="daily"
        )

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
