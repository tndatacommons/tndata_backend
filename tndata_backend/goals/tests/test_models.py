from django.test import TestCase
from django.db.models import QuerySet

from .. models import (
    Category,
    Goal,
    Trigger,
    BehaviorSequence,
    BehaviorAction,
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


class TestBehaviorSequence(TestCase):
    """Tests for the `BehaviorSequence` model."""

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Category Description',
        )
        self.goal = Goal.objects.create(title="Test Goal")
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
