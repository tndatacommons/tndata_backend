from datetime import timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from badgify import commands as badgify_commands
from model_mommy import mommy

from .. badgify_recipes import (
    AchieverRecipe,
    ActionHighFiveRecipe,
    BehaviorCompletedRecipe,
    ConscientiousRecipe,
    CustomActionCompletedRecipe,
    CustomGoalCreatedRecipe,
    ExplorerRecipe,
    FirstTimerRecipe,
    GoalCompletedRecipe,
    GoalSetterRecipe,
    HighFiveRecipe,
    HomecomingRecipe,
    LighthouseRecipe,
    NavigatorRecipe,
    ParticipantRecipe,
    PathfinderRecipe,
    PerfectTenRecipe,
    SeekerRecipe,
    StarterRecipe,
    StreakFiveDaysRecipe,
    StreakFourWeeksRecipe,
    StreakOneWeekRecipe,
    StreakThreeDaysRecipe,
    StreakThreeWeeksRecipe,
    StreakTwoWeeksRecipe,
    StriverRecipe,
    SuperstarRecipe,
    ThoughtfulRecipe,
    TrioRecipe,
    TwoFerRecipe,
    just_joined,
    just_logged_in,
)
from .. models import (
    Action,
    Behavior,
    Category,
    Goal,
    UserAction,
    UserBehavior,
    UserGoal,
    UserCompletedAction,
)


class TestBadgifyHelpers(TestCase):
    """Tests for the helper functions in goals.badgify_recipes."""

    @classmethod
    def setUpTestData(cls):
        # Create our test users
        User = get_user_model()

        now = timezone.now()
        two_hrs = now - timedelta(hours=2)
        yesterday = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)

        # Some brand new users (now & 2 hours ago)
        cls.new1 = mommy.make(User, date_joined=now, last_login=now)
        cls.new2 = mommy.make(User, date_joined=two_hrs, last_login=two_hrs)

        # Some less recent users, with recent logins
        cls.recent1 = mommy.make(User, date_joined=yesterday, last_login=now)
        cls.recent2 = mommy.make(User, date_joined=yesterday, last_login=two_hrs)

        # Some Old users, with recent logins
        cls.old1 = mommy.make(User, date_joined=week_ago, last_login=now)
        cls.old2 = mommy.make(User, date_joined=week_ago, last_login=two_hrs)

        # Set the nth login for each user
        for user in [cls.new1, cls.new2, cls.recent1, cls.recent2]:
            user.userprofile.app_logins = 1
            user.userprofile.save()
        for user in [cls.old1, cls.old2]:
            user.userprofile.app_logins = 2
            user.userprofile.save()

    def test_just_joined(self):
        # Users who joined within the past 10 minutes.
        self.assertEqual(list(just_joined(minutes=10)), [self.new1.id])

        # Users who joined within the past 3 hours.
        self.assertEqual(
            list(just_joined(minutes=180)),
            [self.new1.id, self.new2.id]
        )

        # Users who joined yesterday
        self.assertEqual(
            list(just_joined(days=1)),
            [self.recent1.id, self.recent2.id]
        )

    def test_just_logged_in(self):
        # Users who first logged in within the past 10 minutes.
        self.assertEqual(
            list(just_logged_in(1, minutes=10)),
            [self.new1.id, self.recent1.id]
        )

        # Users who first logged in within the past 3 hours
        expected = [self.new1.id, self.new2.id, self.recent1.id, self.recent2.id]
        self.assertEqual(list(just_logged_in(1, minutes=180)), expected)

        # Users who logged in for the 2nd time within the past 10 minutes
        self.assertEqual(list(just_logged_in(2, minutes=10)), [self.old1.id])

        # Users who logged in for the 2nd time within the past 3 hours
        expected = [self.old1.id, self.old2.id]
        self.assertEqual(list(just_logged_in(2, minutes=180)), expected)


class TestBadgifyRecipes(TestCase):
    """Test that we can create and call the `user_ids` property for all of
    our Badgify Recipe classes.

    NOTE: most of these are just smoke tests, they don't actually construct
    the criteria needed to generate accurate results (see the TODOs)

    """

    @classmethod
    def setUpTestData(cls):
        # Run the badgify setup commands.
        badgify_commands.sync_badges()
        badgify_commands.sync_counts()

        # Create our test data
        User = get_user_model()

        cls.category = mommy.make(Category, state="published")

        cls.goal = mommy.make(Goal, state="published")
        cls.goal.categories.add(cls.category)
        cls.goal.save()

        cls.behavior = mommy.make(Behavior, state="published")
        cls.behavior.goals.add(cls.goal)
        cls.behavior.save()

        cls.action = mommy.make(
            Action, title="Action", state="published", behavior=cls.behavior)
        cls.action2 = mommy.make(
            Action, title="Action2", state="published", behavior=cls.behavior)
        cls.action3 = mommy.make(
            Action, title="Action3", state="published", behavior=cls.behavior)
        cls.action4 = mommy.make(
            Action, title="Action4", state="published", behavior=cls.behavior)
        cls.action5 = mommy.make(
            Action, title="Action5", state="published", behavior=cls.behavior)

        cls.user = User.objects.create_user("badgifyuser", "bu@a.b", "pass")
        cls.user.last_login = timezone.now()  # assume we just logged in.
        cls.user.save()

    def test_starter_recipe(self):
        recipe = StarterRecipe()
        self.assertEqual(list(recipe.user_ids), [self.user.id])

    def test_explorer_recipe(self):
        # TODO: 7 days since singup
        recipe = ExplorerRecipe()
        self.assertIsNotNone(recipe.user_ids)

    def test_lighthouse_recipe(self):
        # TODO: 30 days since singup
        recipe = LighthouseRecipe()
        self.assertIsNotNone(recipe.user_ids)

    def test_homecomeing_recipe(self):
        """When the user has logged in a 2nd time"""
        # Set the user's number of app logins
        original_logins = self.user.userprofile.app_logins
        self.user.userprofile.app_logins = 2
        self.user.userprofile.save()

        # Test the recipe
        recipe = HomecomingRecipe()
        self.assertEqual(list(recipe.user_ids), [self.user.id])

        # reset altered app_logins
        self.user.userprofile.app_logins = original_logins
        self.user.userprofile.save()

    def test_seeker_recipe(self):
        """When the user has logged in a 3rd time"""
        # Set the user's number of app logins
        original_logins = self.user.userprofile.app_logins
        self.user.userprofile.app_logins = 3
        self.user.userprofile.save()

        # Test the recipe
        recipe = SeekerRecipe()
        self.assertEqual(list(recipe.user_ids), [self.user.id])

        # reset altered app_logins
        self.user.userprofile.app_logins = original_logins
        self.user.userprofile.save()

    def test_pathfinder_recipe(self):
        """When the user has logged in a 7th time"""
        # Set the user's number of app logins
        original_logins = self.user.userprofile.app_logins
        self.user.userprofile.app_logins = 7
        self.user.userprofile.save()

        # Test the recipe
        recipe = PathfinderRecipe()
        self.assertEqual(list(recipe.user_ids), [self.user.id])

        # reset altered app_logins
        self.user.userprofile.app_logins = original_logins
        self.user.userprofile.save()

    def test_navigator_recipe(self):
        """When the user has logged in a 14th time"""
        # Set the user's number of app logins
        original_logins = self.user.userprofile.app_logins
        self.user.userprofile.app_logins = 14
        self.user.userprofile.save()

        # Test the recipe
        recipe = NavigatorRecipe()
        self.assertEqual(list(recipe.user_ids), [self.user.id])

        # reset altered app_logins
        self.user.userprofile.app_logins = original_logins
        self.user.userprofile.save()

    def test_thoughtful_recipe(self):
        # TODO: test when the user checks in 1 day in a row.
        recipe = ThoughtfulRecipe()
        self.assertIsNotNone(recipe.user_ids)

    def test_conscientious_recipe(self):
        # TODO: test when the user checks in 2 days in a row.
        recipe = ConscientiousRecipe()
        self.assertIsNotNone(recipe.user_ids)

    def test_streak_three_days_recipe(self):
        # TODO: test when the user checks in 3 days in a row.
        recipe = StreakThreeDaysRecipe()
        self.assertIsNotNone(recipe.user_ids)

    def test_streak_five_days_recipe(self):
        # TODO: test when the user checks in 5 days in a row.
        recipe = StreakFiveDaysRecipe()
        self.assertIsNotNone(recipe.user_ids)

    def test_streak_one_week_recipe(self):
        # TODO: test when the user checks in 7 days in a row.
        recipe = StreakOneWeekRecipe()
        self.assertIsNotNone(recipe.user_ids)

    def test_streak_two_weeks_recipe(self):
        # TODO: test when the user checks in 14 days in a row.
        recipe = StreakTwoWeeksRecipe()
        self.assertIsNotNone(recipe.user_ids)

    def test_streak_three_weeks_recipe(self):
        # TODO: test when the user checks in 21 days in a row.
        recipe = StreakThreeWeeksRecipe()
        self.assertIsNotNone(recipe.user_ids)

    def test_streak_four_weeks_recipe(self):
        # TODO: test when the user checks in 28 days in a row.
        recipe = StreakFourWeeksRecipe()
        self.assertIsNotNone(recipe.user_ids)

    def test_participant_recipe(self):
        # TODO: Test when a user is enrolled in a package.
        recipe = ParticipantRecipe()
        self.assertIsNotNone(recipe.user_ids)

    def test_goal_setter_recipe(self):
        # When a user is enrolled in a goal.
        recipe = GoalSetterRecipe()
        self.user.usergoal_set.create(goal=self.goal)
        self.assertEqual(list(recipe.user_ids), [self.user.id])

    def test_striver_recipe(self):
        # TODO When a user is enrolled in their 2nd goal.
        recipe = StriverRecipe()
        self.assertIsNotNone(recipe.user_ids)

    def test_achiever_recipe(self):
        # TODO When a user is enrolled in their 4th goal.
        recipe = AchieverRecipe()
        self.assertIsNotNone(recipe.user_ids)

    def test_high_five_recipe(self):
        # TODO When a user is enrolled in their 5th goal.
        recipe = HighFiveRecipe()
        self.assertIsNotNone(recipe.user_ids)

    def test_perfect_ten_recipe(self):
        # TODO When a user is enrolled in their 10th goal.
        recipe = PerfectTenRecipe()
        self.assertIsNotNone(recipe.user_ids)

    def test_superstar_recipe(self):
        # TODO When a user is enrolled in their 20th goal.
        recipe = SuperstarRecipe()
        self.assertIsNotNone(recipe.user_ids)

    def test_firsttimer_recipe(self):
        # For a user's first 'got it' (e.g. UserCompletedAction)
        recipe = FirstTimerRecipe()
        ua = UserAction.objects.create(user=self.user, action=self.action)
        UserCompletedAction.objects.create(
            user=self.user,
            useraction=ua,
            action=self.action,
            state=UserCompletedAction.COMPLETED

        )
        self.assertEqual(list(recipe.user_ids), [self.user.id])

        # clean up
        self.user.useraction_set.all().delete()
        self.user.usercompletedaction_set.all().delete()

    def test_twofer_recipe(self):
        # For a user's 2nd 'got it' (e.g. UserCompletedAction)
        recipe = TwoFerRecipe()
        self.assertIsNotNone(recipe.user_ids)

        for action in [self.action, self.action2]:
            ua = UserAction.objects.create(user=self.user, action=action)
            UserCompletedAction.objects.create(
                user=self.user,
                useraction=ua,
                action=action,
                state=UserCompletedAction.COMPLETED

            )
        self.assertEqual(list(recipe.user_ids), [self.user.id])

        # clean up
        self.user.useraction_set.all().delete()
        self.user.usercompletedaction_set.all().delete()

    def test_trio_recipe(self):
        # For a user's 3rd 'got it' (e.g. UserCompletedAction)
        recipe = TrioRecipe()
        self.assertIsNotNone(recipe.user_ids)

        for action in [self.action, self.action2, self.action3]:
            ua = UserAction.objects.create(user=self.user, action=action)
            UserCompletedAction.objects.create(
                user=self.user,
                useraction=ua,
                action=action,
                state=UserCompletedAction.COMPLETED

            )
        self.assertEqual(list(recipe.user_ids), [self.user.id])

        # clean up
        self.user.useraction_set.all().delete()
        self.user.usercompletedaction_set.all().delete()

    def test_action_high_five_recipe(self):
        # For a user's 5th 'got it' (e.g. UserCompletedAction)
        recipe = ActionHighFiveRecipe()
        self.assertIsNotNone(recipe.user_ids)
        actions = [
            self.action, self.action2, self.action3,
            self.action4, self.action5
        ]
        for action in actions:
            ua = UserAction.objects.create(user=self.user, action=action)
            UserCompletedAction.objects.create(
                user=self.user,
                useraction=ua,
                action=action,
                state=UserCompletedAction.COMPLETED

            )
        self.assertEqual(list(recipe.user_ids), [self.user.id])

        # clean up
        self.user.useraction_set.all().delete()
        self.user.usercompletedaction_set.all().delete()

    def test_behavior_completed_recipe(self):
        # When a user completes a behavior.
        recipe = BehaviorCompletedRecipe()
        ub = UserBehavior.objects.create(user=self.user, behavior=self.behavior)
        ub.complete()
        ub.save()
        self.assertEqual(list(recipe.user_ids), [self.user.id])

        # clean up
        ub.delete()

    def test_goal_completed_recipe(self):
        # When a user completes a goal.
        ug = UserGoal.objects.create(user=self.user, goal=self.goal)
        ug.complete()
        ug.save()

        recipe = GoalCompletedRecipe()
        self.assertEqual(list(recipe.user_ids), [self.user.id])

        # clean up
        ug.delete()

    def test_customgoal_created_recipe(self):
        # TODO: when a user creates a Custom Goal
        recipe = CustomGoalCreatedRecipe()
        self.assertIsNotNone(recipe.user_ids)

    def test_customaction_completed_recipe(self):
        # TODO: when a user completes a custom action
        recipe = CustomActionCompletedRecipe()
        self.assertIsNotNone(recipe.user_ids)
