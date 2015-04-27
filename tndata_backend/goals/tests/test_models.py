from django.contrib.auth import get_user_model
from django.test import TestCase
from django.db.models import QuerySet

from .. models import (
    get_categories_as_choices,
    Category,
    Goal,
    Trigger,
    Behavior,
    Action,
    UserGoal,
    UserBehavior,
    UserCategory,
    UserAction,
)

User = get_user_model()


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

    def test_get_categories_as_choices(self):
        """Ensure all categories are returned as a tuple of choices."""
        expected = (
            ("test-category", "Test Category"),
        )
        self.assertEqual(get_categories_as_choices(), expected)

    def test_save(self):
        """Verify that saving generates a title_slug"""
        category = Category.objects.create(order=2, title="New Name")
        category.save()
        self.assertEqual(category.title_slug, "new-name")
        category.delete()  # Clean up.

    def test_save_created_by(self):
        """Allow passing an `created_by` param into save."""
        u = User.objects.create_user('user', 'u@example.com', 'secret')
        c = Category(order=3, title="New")
        c.save(created_by=u)
        self.assertEqual(c.created_by, u)
        u.delete()  # Clean up
        c.delete()

    def test_save_updated_by(self):
        """Allow passing an `updated_by` param into save."""
        u = User.objects.create_user('user', 'u@example.com', 'secret')
        self.category.save(updated_by=u)
        self.assertEqual(self.category.updated_by, u)
        u.delete()  # Clean up

    def test_goals(self):
        self.assertIsInstance(self.category.goals, QuerySet)

    def test_get_absolute_url(self):
        self.assertEqual(
            self.category.get_absolute_url(),
            "/goals/categories/test-category/"
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.category.get_update_url(),
            "/goals/categories/test-category/update/"
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.category.get_delete_url(),
            "/goals/categories/test-category/delete/"
        )

    def test_default_state(self):
        """Ensure that the default state is 'draft'."""
        self.assertEqual(self.category.state, "draft")

    def test_review(self):
        self.category.review()  # Switch to pending-review
        self.assertEqual(self.category.state, "pending-review")

    def test_decline(self):
        self.category.review()  # Switch to pending-review
        self.category.decline()  # then decline
        self.assertEqual(self.category.state, "declined")

    def test_publish(self):
        self.category.review()  # Switch to pending-review
        self.category.publish()  # then publish
        self.assertEqual(self.category.state, "published")

    def test_publish_from_draft(self):
        self.assertEqual(self.category.state, "draft")
        self.category.publish()  # then publish
        self.assertEqual(self.category.state, "published")


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

    def test_save_created_by(self):
        """Allow passing an `created_by` param into save."""
        u = User.objects.create_user('user', 'u@example.com', 'secret')
        g = Goal(title="New")
        g.save(created_by=u)
        self.assertEqual(g.created_by, u)
        u.delete()  # Clean up
        g.delete()

    def test_save_updated_by(self):
        """Allow passing an `updated_by` param into save."""
        u = User.objects.create_user('user', 'u@example.com', 'secret')
        self.goal.save(updated_by=u)
        self.assertEqual(self.goal.updated_by, u)
        u.delete()  # Clean up

    def test_get_absolute_url(self):
        self.assertEqual(
            self.goal.get_absolute_url(),
            "/goals/goals/title-for-test-goal/"
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.goal.get_update_url(),
            "/goals/goals/title-for-test-goal/update/"
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.goal.get_delete_url(),
            "/goals/goals/title-for-test-goal/delete/"
        )

    def test_default_state(self):
        """Ensure that the default state is 'draft'."""
        self.assertEqual(self.goal.state, "draft")

    def test_review(self):
        self.goal.review()  # Switch to pending-review
        self.assertEqual(self.goal.state, "pending-review")

    def test_decline(self):
        self.goal.review()  # Switch to pending-review
        self.goal.decline()  # then decline
        self.assertEqual(self.goal.state, "declined")

    def test_publish(self):
        self.goal.review()  # Switch to pending-review
        self.goal.publish()  # then publish
        self.assertEqual(self.goal.state, "published")

    def test_publish_from_draft(self):
        self.assertEqual(self.goal.state, "draft")
        self.goal.publish()  # then publish
        self.assertEqual(self.goal.state, "published")


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
            "/goals/triggers/test-trigger/"
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.trigger.get_update_url(),
            "/goals/triggers/test-trigger/update/"
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.trigger.get_delete_url(),
            "/goals/triggers/test-trigger/delete/"
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
        self.assertEqual(behavior.title_slug, "new-name")

    def test_save_created_by(self):
        """Allow passing an `created_by` param into save."""
        u = User.objects.create_user('user', 'u@example.com', 'secret')
        b = Behavior(title="New")
        b.save(created_by=u)
        self.assertEqual(b.created_by, u)
        u.delete()  # Clean up
        b.delete()

    def test_save_updated_by(self):
        """Allow passing an `updated_by` param into save."""
        u = User.objects.create_user('user', 'u@example.com', 'secret')
        self.behavior.save(updated_by=u)
        self.assertEqual(self.behavior.updated_by, u)
        u.delete()  # Clean up

    def test_get_absolute_url(self):
        self.assertEqual(
            self.behavior.get_absolute_url(),
            "/goals/behaviors/test-behavior/"
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.behavior.get_update_url(),
            "/goals/behaviors/test-behavior/update/"
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.behavior.get_delete_url(),
            "/goals/behaviors/test-behavior/delete/"
        )

    def test_default_state(self):
        """Ensure that the default state is 'draft'."""
        self.assertEqual(self.behavior.state, "draft")

    def test_review(self):
        self.behavior.review()  # Switch to pending-review
        self.assertEqual(self.behavior.state, "pending-review")

    def test_decline(self):
        self.behavior.review()  # Switch to pending-review
        self.behavior.decline()  # then decline
        self.assertEqual(self.behavior.state, "declined")

    def test_publish(self):
        self.behavior.review()  # Switch to pending-review
        self.behavior.publish()  # then publish
        self.assertEqual(self.behavior.state, "published")

    def test_publish_from_draft(self):
        self.assertEqual(self.behavior.state, "draft")
        self.behavior.publish()  # then publish
        self.assertEqual(self.behavior.state, "published")


class TestAction(TestCase):
    """Tests for the `Action` model."""

    def setUp(self):
        self.behavior = Behavior.objects.create(
            title='Test Behavior'
        )
        self.action = Action.objects.create(
            behavior=self.behavior,
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
        action = Action.objects.create(behavior=self.behavior, title="New Name")
        action.save()
        self.assertEqual(action.title_slug, "new-name")

    def test_save_created_by(self):
        """Allow passing an `created_by` param into save."""
        u = User.objects.create_user('user', 'u@example.com', 'secret')
        a = Action(title="New", behavior=self.behavior)
        a.save(created_by=u)
        self.assertEqual(a.created_by, u)
        u.delete()  # Clean up
        a.delete()

    def test_save_updated_by(self):
        """Allow passing an `updated_by` param into save."""
        u = User.objects.create_user('user', 'u@example.com', 'secret')
        self.action.save(updated_by=u)
        self.assertEqual(self.action.updated_by, u)
        u.delete()  # Clean up

    def test_get_absolute_url(self):
        self.assertEqual(
            self.action.get_absolute_url(),
            "/goals/actions/test-action/"
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.action.get_update_url(),
            "/goals/actions/test-action/update/"
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.action.get_delete_url(),
            "/goals/actions/test-action/delete/"
        )

    def test_default_state(self):
        """Ensure that the default state is 'draft'."""
        self.assertEqual(self.action.state, "draft")

    def test_review(self):
        self.action.review()  # Switch to pending-review
        self.assertEqual(self.action.state, "pending-review")

    def test_decline(self):
        self.action.review()  # Switch to pending-review
        self.action.decline()  # then decline
        self.assertEqual(self.action.state, "declined")

    def test_publish(self):
        self.action.review()  # Switch to pending-review
        self.action.publish()  # then publish
        self.assertEqual(self.action.state, "published")

    def test_publish_from_draft(self):
        self.assertEqual(self.action.state, "draft")
        self.action.publish()  # then publish
        self.assertEqual(self.action.state, "published")


class TestUserGoal(TestCase):
    """Tests for the `UserGoal` model."""

    def setUp(self):
        self.user, created = User.objects.get_or_create(
            username="test",
            email="test@example.com"
        )
        self.goal = Goal.objects.create(
            title='Test Goal',
            subtitle="Test Subtitle",

        )
        self.ug = UserGoal.objects.create(
            user=self.user,
            goal=self.goal
        )

    def tearDown(self):
        User.objects.filter(id=self.user.id).delete()
        Goal.objects.filter(id=self.goal.id).delete()
        UserGoal.objects.filter(id=self.ug.id).delete()

    def test__str__(self):
        expected = "Test Goal"
        actual = "{}".format(self.ug)
        self.assertEqual(expected, actual)


class TestUserBehavior(TestCase):
    """Tests for the `UserBehavior` model."""

    def setUp(self):
        self.user, created = User.objects.get_or_create(
            username="test",
            email="test@example.com"
        )
        self.behavior = Behavior.objects.create(title='Test Behavior')
        self.ub = UserBehavior.objects.create(
            user=self.user,
            behavior=self.behavior
        )

    def tearDown(self):
        User.objects.filter(id=self.user.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()
        UserBehavior.objects.filter(id=self.ub.id).delete()

    def test__str__(self):
        expected = "Test Behavior"
        actual = "{}".format(self.ub)
        self.assertEqual(expected, actual)


class TestUserAction(TestCase):
    """Tests for the `UserAction` model."""

    def setUp(self):
        self.user, created = User.objects.get_or_create(
            username="test",
            email="test@example.com"
        )
        self.behavior = Behavior.objects.create(title='Test Behavior')
        self.action = Action.objects.create(
            title='Test Action',
            behavior=self.behavior
        )
        self.ua = UserAction.objects.create(
            user=self.user,
            action=self.action
        )

    def tearDown(self):
        User.objects.filter(id=self.user.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()
        Action.objects.filter(id=self.action.id).delete()
        UserAction.objects.filter(id=self.ua.id).delete()

    def test__str__(self):
        expected = "Test Action"
        actual = "{}".format(self.ua)
        self.assertEqual(expected, actual)


class TestUserCategory(TestCase):
    """Tests for the `UserCategory` model."""

    def setUp(self):
        self.user, created = User.objects.get_or_create(
            username="test",
            email="test@example.com"
        )
        self.category = Category.objects.create(
            title='Test Category',
            order=1,
        )
        self.uc = UserCategory.objects.create(
            user=self.user,
            category=self.category
        )

    def tearDown(self):
        User.objects.filter(id=self.user.id).delete()
        Category.objects.filter(id=self.category.id).delete()
        UserCategory.objects.filter(id=self.uc.id).delete()

    def test__str__(self):
        expected = "Test Category"
        actual = "{}".format(self.uc)
        self.assertEqual(expected, actual)
