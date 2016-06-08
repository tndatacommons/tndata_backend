from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from badgify import commands as badgify_commands
from model_mommy import mommy

from .. badgify_recipes import (
    AchieverRecipe,
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
        # TODO For a user's first 'got it' (e.g. UserCompletedAction)
        recipe = FirstTimerRecipe()
        ua = UserAction.objects.create(user=self.user, action=self.action)
        uca = UserCompletedAction.objects.create(
            user=self.user,
            useraction=ua,
            action=self.action
        )
        self.assertEqual(list(recipe.user_ids), [self.user.id])

        # clean up
        uca.delete()
        ua.delete()

    def test_twofer_recipe(self):
        # TODO For a user's 2nd 'got it' (e.g. UserCompletedAction)
        recipe = TwoFerRecipe()
        self.assertIsNotNone(recipe.user_ids)

    def test_trio_recipe(self):
        # TODO For a user's 3rd 'got it' (e.g. UserCompletedAction)
        recipe = TrioRecipe()
        self.assertIsNotNone(recipe.user_ids)

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
