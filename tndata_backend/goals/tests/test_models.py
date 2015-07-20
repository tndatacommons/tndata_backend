from datetime import datetime, date, time
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.db.models import QuerySet
from django.utils import timezone

from .. models import (
    Action,
    Behavior,
    BehaviorProgress,
    Category,
    CategoryProgress,
    Goal,
    GoalProgress,
    Trigger,
    UserAction,
    UserBehavior,
    UserCategory,
    UserGoal,
    get_categories_as_choices,
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

    def test_behaviors(self):
        self.assertIsInstance(self.category.behaviors, QuerySet)

    def test__format_color(self):
        self.assertEqual(self.category._format_color("ffaabb"), "#ffaabb")
        self.assertEqual(self.category._format_color("#ffaabb"), "#ffaabb")

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

    @classmethod
    def setUpTestData(cls):
        cls.trigger = Trigger.objects.create(
            name="Test Trigger",
            trigger_type="time",
            time=time(12, 34),
            recurrences="RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR",
        )

    def test_recurrences_formats(self):
        """Test various recurrences formats"""
        payload = {
            "name": "A",
            "trigger_type": "time",
            "time": time(12, 34),
            "recurrences": "RRULE:FREQ=DAILY"
        }
        t = Trigger.objects.create(**payload)
        self.assertEqual(t.serialized_recurrences(), "RRULE:FREQ=DAILY")

        payload["name"] = "B"
        payload["recurrences"] = "RRULE:FREQ=WEEKLY;WKST=SU;BYDAY=MO,TU,WE,TH,FR"
        t = Trigger.objects.create(**payload)
        self.assertEqual(
            t.serialized_recurrences(),
            "RRULE:FREQ=WEEKLY;WKST=SU;BYDAY=MO,TU,WE,TH,FR"
        )

    def test__str__(self):
        expected = "Test Trigger  12:34 weekly, each Monday, Tuesday, Wednesday, Thursday, Friday"
        actual = "{}".format(self.trigger)
        self.assertEqual(expected, actual)

    def test__localize_time(self):
        t = Trigger(name="X", trigger_type="time", time=time(12, 34))
        self.assertEqual(t.time, time(12, 34))
        t._localize_time()
        self.assertEqual(t.time, time(12, 34, tzinfo=timezone.utc))

    def test_save(self):
        """Verify that saving generates a name_slug"""
        trigger = Trigger.objects.create(name="New Name", trigger_type="time")
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

    def test_recurrences_as_text(self):
        expected = "weekly, each Monday, Tuesday, Wednesday, Thursday, Friday"
        self.assertEqual(self.trigger.recurrences_as_text(), expected)

    def test_next(self):
        """Ensure that next returns the next day's event."""
        # returns none when trigger_type == 'place'
        self.trigger.trigger_type = "place"
        self.trigger.save()
        self.assertIsNone(self.trigger.next())

        # Reset to time triggers
        self.trigger.trigger_type = "time"
        self.trigger.save()

        # returns none when there's no recurrence & no date
        self.assertIsNone(Trigger(trigger_type="time").next())

        with patch("goals.models.timezone.now") as mock_now:
            mock_now.return_value = datetime(
                1000, 10, 20, 9, 30, 45, tzinfo=timezone.utc
            )
            # Expected is in exactly 1 day
            expected = datetime(1000, 10, 21, 12, 34, tzinfo=timezone.utc)
            self.assertEqual(self.trigger.next(), expected)

    def test_next_when_no_recurrence(self):
        trigger = Trigger.objects.create(
            name="Date-Trigger",
            trigger_type="time",
            time=time(12, 34),
            trigger_date=date(2222, 3, 15),
        )

        expected = datetime.combine(date(2222, 3, 15), time(12, 34))
        expected = timezone.make_aware(expected, timezone=timezone.utc)
        self.assertEqual(trigger.next(), expected)


class TestBehavior(TestCase):
    """Tests for the `Behavior` model."""

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Category Description',
        )
        self.goal = Goal.objects.create(title="Test Goal")
        self.goal.categories.add(self.category)
        self.behavior = Behavior.objects.create(
            title='Test Behavior',
        )
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

    # TODO: need to include a test case for actions with duplicate titles/slugs
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
            "/goals/actions/{0}-test-action/".format(self.action.id)
        )

    def test_get_update_url(self):
        self.assertEqual(
            self.action.get_update_url(),
            "/goals/actions/{0}-test-action/update/".format(self.action.id)
        )

    def test_get_delete_url(self):
        self.assertEqual(
            self.action.get_delete_url(),
            "/goals/actions/{0}-test-action/delete/".format(self.action.id)
        )

    def test_get_create_starter_action_url(self):
        self.assertEqual(
            Action.get_create_starter_action_url(),
            "/goals/new/action/?actiontype={0}".format(Action.STARTER)
        )

    def test_get_create_tiny_action_url(self):
        self.assertEqual(
            Action.get_create_tiny_action_url(),
            "/goals/new/action/?actiontype={0}".format(Action.TINY)
        )

    def test_get_create_resource_action_url(self):
        self.assertEqual(
            Action.get_create_resource_action_url(),
            "/goals/new/action/?actiontype={0}".format(Action.RESOURCE)
        )

    def test_get_create_now_action_url(self):
        self.assertEqual(
            Action.get_create_now_action_url(),
            "/goals/new/action/?actiontype={0}".format(Action.NOW)
        )

    def test_get_create_later_action_url(self):
        self.assertEqual(
            Action.get_create_later_action_url(),
            "/goals/new/action/?actiontype={0}".format(Action.LATER)
        )

    def test_get_create_custom_action_url(self):
        self.assertEqual(
            Action.get_create_custom_action_url(),
            "/goals/new/action/?actiontype={0}".format(Action.CUSTOM)
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

    def test_progress_value(self):
        # we haven't created any GoalProgress data, so this should be zero
        self.assertEqual(self.ug.progress_value, 0.0)


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


class TestBehaviorProgress(TestCase):
    """Tests for the `BehaviorProgress` model."""

    @classmethod
    def setUpTestData(cls):
        cls.user, created = User.objects.get_or_create(
            username="test",
            email="test@example.com"
        )
        cls.behavior = Behavior.objects.create(title='Test Behavior')
        cls.ub = UserBehavior.objects.create(
            user=cls.user,
            behavior=cls.behavior
        )
        cls.progress = BehaviorProgress.objects.create(
            user=cls.user,
            user_behavior=cls.ub,
            status=BehaviorProgress.ON_COURSE
        )

    def test__str__(self):
        self.assertEqual("On Course", "{}".format(self.progress))

    def test_status_display(self):
        self.assertEqual(self.progress.status_display, "On Course")

    def test_behavior(self):
        self.assertEqual(self.progress.behavior, self.behavior)


class TestGoalProgress(TestCase):
    """Tests for the `GoalProgress` model."""

    @classmethod
    def setUpTestData(cls):
        cls.user, created = User.objects.get_or_create(
            username="test",
            email="test@example.com"
        )
        cls.goal = Goal.objects.create(title="Test Goal", description="Desc")
        cls.ug = UserGoal.objects.create(user=cls.user, goal=cls.goal)

        cls.behavior = Behavior.objects.create(title='Test Behavior')
        cls.behavior.goals.add(cls.goal)
        cls.ub = UserBehavior.objects.create(
            user=cls.user,
            behavior=cls.behavior
        )
        # Create some progress items toward this User's Behavior
        data = {
            'user': cls.user,
            'user_behavior': cls.ub,
            'status': BehaviorProgress.ON_COURSE
        }
        BehaviorProgress.objects.create(**data)

        data['status'] = BehaviorProgress.SEEKING
        BehaviorProgress.objects.create(**data)

        data['status'] = BehaviorProgress.OFF_COURSE
        BehaviorProgress.objects.create(**data)

        # Create a GoalProgress by generating the scores.
        cls.gp = GoalProgress.objects.generate_scores(cls.user).latest()

    def test_expected_values(self):
        """Ensure the score components contain the expected values."""
        self.assertEqual(self.gp.current_total, 6)  # 3 + 2 + 1
        self.assertEqual(self.gp.max_total, 9)  # 3 * 3
        self.assertEqual(self.gp.current_score, 0.67)  # round(6/9, 2)

    def test__str__(self):
        self.assertEqual("0.67", "{}".format(self.gp))

    def test__calculate_value(self):
        """Ensure that this method calculates the score."""
        expected = round(self.gp.current_total / self.gp.max_total, 2)
        self.gp._calculate_score()
        self.assertEqual(self.gp.current_score, expected)

    def test_save(self):
        """Saving an object should calculate it's score"""
        original = self.gp._calculate_score
        self.gp._calculate_score = Mock()
        self.gp.save()
        self.gp._calculate_score.assert_called_once_with()
        self.gp._calculate_score = original

    def test_text_glyph(self):
        self.assertEqual(self.gp.text_glyph, u"\u2192")


class TestCategoryProgress(TestCase):
    """Tests for the `CategoryProgress` model."""

    @classmethod
    def setUpTestData(cls):
        cls.user, created = User.objects.get_or_create(
            username="test",
            email="test@example.com"
        )
        cls.category = Category.objects.create(
            order=5,
            title="Test Category",
            description="Desc"
        )
        cls.uc = UserCategory.objects.create(user=cls.user, category=cls.category)

        # create a goal and a fake GoalProgress
        cls.goal = Goal.objects.create(title="G", description="G.")
        cls.goal.categories.add(cls.category)
        cls.ug = UserGoal.objects.create(user=cls.user, goal=cls.goal)
        cls.gp = GoalProgress.objects.create(
            user=cls.user,
            goal=cls.goal,
            current_score=0.33,
            current_total=3.0,
            max_total=9.0,
        )

        # Create a CategoryProgress by generating the scores.
        progress = CategoryProgress.objects.generate_scores(cls.user)
        cls.cp = progress.latest()

    def test_expected_values(self):
        """Ensure the score components contain the expected values."""
        self.assertEqual(self.cp.current_score, 0.33)  # round(3/9, 2)

    def test__str__(self):
        self.assertEqual("0.33", "{}".format(self.cp))

    def test_text_glyph(self):
        self.assertEqual(self.cp.text_glyph, u"\u2198")
