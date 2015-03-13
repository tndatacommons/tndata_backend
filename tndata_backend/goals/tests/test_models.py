from django.test import TestCase
from django.db.models import QuerySet

from .. models import (
    Category,
    Goal,
    Trigger,
    Behavior,
    Action,
)


class TestCategory(TestCase):
    """Tests for the `Category` model."""

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )

    def tearDown(self):
        Category.objects.filter(id=self.category.id).delete()

    def test__str__(self):
        expected = "Test Category"
        actual = "{}".format(self.category)
        self.assertEqual(expected, actual)

    def test_save(self):
        """Verify that saving generates a title_slug"""
        category = Category.objects.create(order=2, title="New Name")
        category.save()
        self.assertEqual(category.title_slug, "new-name")

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
            title='Test Category',
            description='Category Description',
        )
        self.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
            outcome="An Outcome"
        )
        self.goal.categories.add(self.category)

    def tearDown(self):
        Goal.objects.filter(id=self.goal.id).delete()
        Category.objects.filter(id=self.category.id).delete()

    def test__str__(self):
        expected = "Title for Test Goal"
        actual = "{}".format(self.goal)
        self.assertEqual(expected, actual)

    def test_save(self):
        """Verify that saving generates a name_slug"""
        goal = Goal.objects.create(title="New Name")
        goal.save()
        self.assertEqual(goal.title_slug, "new-name")

    def test_get_absolute_url(self):
        self.assertEqual(
            self.goal.get_absolute_url(),
            "/goals/goal/title-for-test-goal/"
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.goal.get_update_url(),
            "/goals/goal/title-for-test-goal/update/"
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.goal.get_delete_url(),
            "/goals/goal/title-for-test-goal/delete/"
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


class TestBehavior(TestCase):
    """Tests for the `Behavior` model."""

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Category Description',
        )
        self.goal = Goal.objects.create(title="Test Goal")
        self.behavior = Behavior.objects.create(
            title='Test Behavior',
        )
        self.behavior.categories.add(self.category)
        self.behavior.goals.add(self.goal)

    def tearDown(self):
        Category.objects.filter(id=self.category.id).delete()
        Goal.objects.filter(id=self.goal.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()

    def test__str__(self):
        expected = "Test Behavior"
        actual = "{}".format(self.behavior)
        self.assertEqual(expected, actual)

    def test_save(self):
        """Verify that saving generates a title_slug"""
        behavior = Behavior.objects.create(title="New Name")
        behavior.save()
        self.assertEqual(bs.title_slug, "new-name")

    def test_get_absolute_url(self):
        self.assertEqual(
            self.behavior.get_absolute_url(),
            "/goals/behavior/test-behavior/"
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.behavior.get_update_url(),
            "/goals/behavior/test-behavior/update/"
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.behavior.get_delete_url(),
            "/goals/behavior/test-behavior/delete/"
        )


class TestAction(TestCase):
    """Tests for the `Action` model."""

    def setUp(self):
        self.behavior = Behavior.objects.create(
            title='Test Behavior'
        )
        self.action = Action.objects.create(
            sequence=self.behavior,
            title="Test Action"
        )

    def tearDown(self):
        Behavior.objects.filter(id=self.behavior.id).delete()
        Action.objects.filter(id=self.action.id).delete()

    def test__str__(self):
        expected = "Test Action"
        actual = "{}".format(self.action)
        self.assertEqual(expected, actual)

    def test_save(self):
        """Verify that saving generates a name_slug"""
        action = Action.objects.create(sequence=self.behavior, title="New Name")
        action.save()
        self.assertEqual(action.title_slug, "new-name")

    def test_get_absolute_url(self):
        self.assertEqual(
            self.action.get_absolute_url(),
            "/goals/action/test-action/"
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.action.get_update_url(),
            "/goals/action/test-action/update/"
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.action.get_delete_url(),
            "/goals/action/test-action/delete/"
        )
