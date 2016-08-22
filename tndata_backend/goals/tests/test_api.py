from datetime import date, time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from .. models import (
    Action,
    Behavior,
    Category,
    CustomAction,
    CustomActionFeedback,
    CustomGoal,
    Goal,
    PackageEnrollment,
    Trigger,
    UserGoal,
    UserBehavior,
    UserCategory,
    UserAction,
    UserCompletedAction,
    UserCompletedCustomAction,
)


# XXX We've got each test case in this module decorated with `override_settings`,
# XXX though I'm not sure that actually works with APITestCase
# XXX See: https://github.com/tomchristie/django-rest-framework/issues/2466
DRF_DT_FORMAT = settings.REST_FRAMEWORK['DATETIME_FORMAT']
TEST_SESSION_ENGINE = 'django.contrib.sessions.backends.db'
TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
TEST_REST_FRAMEWORK = {
    'PAGE_SIZE': 100,
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'utils.api.BrowsableAPIRendererWithoutForms',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'utils.api.NoThrottle',
    ),
    'VERSION_PARAM': 'version',
    'DEFAULT_VERSION': '1',
    'ALLOWED_VERSIONS': ['1', '2'],
    'DEFAULT_VERSIONING_CLASS': 'utils.api.DefaultQueryParamVersioning',
    'DATETIME_FORMAT': DRF_DT_FORMAT,
}


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestCategoryAPI(APITestCase):

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
            notes="Some notes",
        )
        self.category.publish()
        self.category.save()

    def tearDown(self):
        Category.objects.filter(id=self.category.id).delete()

    def test_get_category_list(self):
        url = reverse('category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        c = response.data['results'][0]
        self.assertEqual(c['id'], self.category.id)
        self.assertEqual(c['description'], self.category.description)
        self.assertEqual(c['html_description'], self.category.rendered_description)
        self.assertEqual(c['title'], self.category.title)
        self.assertEqual(c['title_slug'], self.category.title_slug)
        self.assertEqual(c['icon_url'], self.category.get_absolute_icon())
        self.assertEqual(c['image_url'], self.category.get_absolute_image())
        self.assertEqual(c['goals_count'], self.category.goals.count())
        self.assertFalse(c['packaged_content'])

    def test_post_category_list(self):
        """Ensure this endpoint is read-only."""
        url = reverse('category-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_category_detail(self):
        url = reverse('category-detail', args=[self.category.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.category.id)

    def test_post_category_detail(self):
        """Ensure this endpoint is read-only."""
        url = reverse('category-detail', args=[self.category.id])
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestGoalAPI(APITestCase):

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
            notes="Some notes",
        )
        self.category.publish()
        self.category.save()
        self.goal = Goal.objects.create(
            title="Test Goal",
            subtitle="A subtitle",
            description="A Description",
        )
        self.goal.categories.add(self.category)
        self.goal.publish()
        self.goal.save()

    def tearDown(self):
        Category.objects.filter(id=self.category.id).delete()
        Goal.objects.filter(id=self.goal.id).delete()

    def test_goal_list(self):
        url = reverse('goal-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        obj = response.data['results'][0]
        self.assertEqual(obj['id'], self.goal.id)
        self.assertEqual(obj['title'], self.goal.title)
        self.assertEqual(obj['title_slug'], self.goal.title_slug)
        self.assertEqual(obj['description'], self.goal.description)
        self.assertEqual(obj['html_description'], self.goal.rendered_description)
        self.assertEqual(obj['behaviors_count'], self.goal.behavior_set.count())
        # Check the SimpleCategorySerializer used with goals
        self.assertIn('categories', obj)
        self.assertIn("image_url", obj['categories'][0])
        self.assertIn("icon_url", obj['categories'][0])

    def test_goal_list_by_category(self):
        """Ensure we can filter by category."""
        # Create another Goal (not in a catgory)
        c = Category.objects.create(order=2, title="Other")
        c.publish()
        c.save()

        g = Goal.objects.create(title="ignore me")
        g.categories.add(c)
        g.publish()
        g.save()

        url = reverse('goal-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # Our other goal is here

        # Check the filtered result
        url = "{0}?category={1}".format(url, self.category.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.goal.id)

        # Clean up.
        g.delete()

    def test_post_goal_list(self):
        """Ensure this endpoint is read-only."""
        url = reverse('goal-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_goal_detail(self):
        url = reverse('goal-detail', args=[self.goal.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.goal.id)

    def test_post_goal_detail(self):
        """Ensure this endpoint is read-only."""
        url = reverse('goal-detail', args=[self.goal.id])
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestTriggerAPI(APITestCase):
    """Since v1 is technically going to be depricated, and this endpoint was
    never really used, this is just a smoke-screen test for unauthed access."""

    def test_get_trigger_list(self):
        response = self.client.get(reverse('trigger-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_trigger_list(self):
        """Ensure this endpoint is read-only."""
        response = self.client.post(reverse('trigger-list'), {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_trigger_detail(self):
        response = self.client.get(reverse('trigger-detail', args=[1]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_trigger_detail(self):
        response = self.client.put(reverse('trigger-detail', args=[1]), {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestBehaviorAPI(APITestCase):

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
            notes="Some notes"
        )
        self.category.publish()
        self.category.save()

        self.goal = Goal.objects.create(
            title="Test Goal",
            subtitle="A subtitle",
            description="A Description",
        )
        self.goal.categories.add(self.category)
        self.goal.publish()
        self.goal.save()

        self.behavior = Behavior.objects.create(
            title="Test Behavior",
            description="This is a test",
            informal_list="Do this",
            more_info="* a bullet"
        )
        self.behavior.goals.add(self.goal)
        self.behavior.publish()
        self.behavior.save()

    def tearDown(self):
        Category.objects.filter(id=self.category.id).delete()
        Goal.objects.filter(id=self.goal.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()

    def test_behavior_list(self):
        url = reverse('behavior-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        obj = response.data['results'][0]
        self.assertEqual(obj['id'], self.behavior.id)
        self.assertEqual(obj['title'], self.behavior.title)
        self.assertEqual(obj['title_slug'], self.behavior.title_slug)
        self.assertEqual(obj['description'], self.behavior.description)
        self.assertEqual(obj['html_description'], self.behavior.rendered_description)
        self.assertEqual(obj['more_info'], self.behavior.more_info)
        self.assertEqual(obj['html_more_info'], self.behavior.rendered_more_info)
        self.assertEqual(len(obj['goals']), 1)  # Should have 1 goal
        self.assertEqual(obj['goals'][0]['title'], self.goal.title)
        self.assertEqual(obj['actions_count'], self.behavior.action_set.count())

    def test_behavior_list_by_category_id(self):
        """Ensure we can filter by category.id."""
        # Create another Behavior (with no Category)
        b = Behavior.objects.create(title="ignore me")
        b.publish()
        b.save()

        url = reverse('behavior-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}?category={1}".format(url, self.category.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.behavior.id)

        # Clean up.
        b.delete()

    def test_behavior_list_by_category_title_slug(self):
        """Ensure we can filter by category.title_slug."""
        # Create another Behavior (with no Category)
        b = Behavior.objects.create(title="ignore me")
        b.publish()
        b.save()

        url = reverse('behavior-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}?category={1}".format(url, self.category.title_slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.behavior.id)

        # Clean up.
        b.delete()

    def test_behavior_list_by_goal_id(self):
        """Ensure we can filter by goal.id"""
        # Create another Behavior (with no Goal)
        b = Behavior.objects.create(title="ignore me")
        b.publish()
        b.save()

        url = reverse('behavior-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}?goal={1}".format(url, self.goal.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.behavior.id)

        # Clean up.
        b.delete()

    def test_behavior_list_by_goal_title_slug(self):
        """Ensure we can filter by goal.title_slug"""
        # Create another Behavior (with no Goal)
        b = Behavior.objects.create(title="ignore me")
        b.publish()
        b.save()

        url = reverse('behavior-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}?goal={1}".format(url, self.goal.title_slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.behavior.id)

        # Clean up.
        b.delete()

    def test_post_behavior_list(self):
        """Ensure this endpoint is read-only."""
        url = reverse('behavior-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_behavior_detail(self):
        url = reverse('behavior-detail', args=[self.behavior.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.behavior.id)

    def test_post_behavior_detail(self):
        """Ensure this endpoint is read-only."""
        url = reverse('behavior-detail', args=[self.behavior.id])
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestActionAPI(APITestCase):

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
            notes="Some notes"
        )
        self.category.publish()
        self.category.save()

        self.goal = Goal.objects.create(
            title="Test Goal",
            subtitle="A subtitle",
            description="A Description",
        )
        self.goal.categories.add(self.category)
        self.goal.publish()
        self.goal.save()

        self.behavior = Behavior.objects.create(
            title="Test Behavior",
            description="This is a test",
            informal_list="Do this",
        )
        self.behavior.goals.add(self.goal)
        self.behavior.publish()
        self.behavior.save()

        self.action = Action.objects.create(
            title="Test Action",
            sequence_order=1,
            behavior=self.behavior,
            description="This is a test",
            more_info="* a bullet"
        )
        self.action.publish()
        self.action.save()

    def tearDown(self):
        Category.objects.filter(id=self.category.id).delete()
        Goal.objects.filter(id=self.goal.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()
        Action.objects.filter(id=self.action.id).delete()

    def test_action_list(self):
        url = reverse('action-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        obj = response.data['results'][0]
        self.assertEqual(obj['id'], self.action.id)
        self.assertEqual(obj['title'], self.action.title)
        self.assertEqual(obj['title_slug'], self.action.title_slug)
        self.assertEqual(obj['description'], self.action.description)
        self.assertEqual(obj['html_description'], self.action.rendered_description)
        self.assertEqual(obj['more_info'], self.action.more_info)
        self.assertEqual(obj['html_more_info'], self.action.rendered_more_info)
        self.assertEqual(obj['behavior']['id'], self.behavior.id)

    def test_action_list_by_category_id(self):
        """Ensure we can filter by category.id."""
        # Create another Action (with no Category)
        b = Behavior.objects.create(title='ignore me')
        b.publish()
        b.save()

        a = Action.objects.create(title="ignore me", behavior=b)
        a.publish()
        a.save()

        url = reverse('action-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}?category={1}".format(url, self.category.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.action.id)

        # Clean up.
        a.delete()
        b.delete()

    def test_action_list_by_category_title_slug(self):
        """Ensure we can filter by category.title_slug."""
        # Create another Action (with no Category)
        b = Behavior.objects.create(title='ignore me')
        b.publish()
        b.save()

        a = Action.objects.create(title="ignore me", behavior=b)
        a.publish()
        a.save()

        url = reverse('action-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}?category={1}".format(url, self.category.title_slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.action.id)

        # Clean up.
        a.delete()
        b.delete()

    def test_action_list_by_goal_id(self):
        """Ensure we can filter by goal.id"""
        # Create another Action (with no Goal)
        b = Behavior.objects.create(title='ignore me')
        b.publish()
        b.save()

        a = Action.objects.create(title="ignore me", behavior=b)
        a.publish()
        a.save()

        url = reverse('action-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}?goal={1}".format(url, self.goal.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.action.id)

        # Clean up.
        a.delete()
        b.delete()

    def test_action_list_by_goal_title_slug(self):
        """Ensure we can filter by goal.title_slug"""
        # Create another Action (with no Goal)
        b = Behavior.objects.create(title='ignore me')
        b.publish()
        b.save()

        a = Action.objects.create(title="ignore me", behavior=b)
        a.publish()
        a.save()

        url = reverse('action-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}?goal={1}".format(url, self.goal.title_slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.action.id)

        # Clean up.
        a.delete()
        b.delete()

    def test_action_list_by_behavior_id(self):
        """Ensure we can filter by behavior.id"""
        # Create another Action
        b = Behavior.objects.create(title='ignore me')
        b.publish()
        b.save()

        a = Action.objects.create(title="ignore me", behavior=b)
        a.publish()
        a.save()

        url = reverse('action-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}?behavior={1}".format(url, self.behavior.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.action.id)

        # Clean up.
        a.delete()
        b.delete()

    def test_action_list_by_behavior_title_slug(self):
        """Ensure we can filter by behavior.title_slug"""
        # Create another Action
        b = Behavior.objects.create(title='ignore me')
        b.publish()
        b.save()

        a = Action.objects.create(title="ignore me", behavior=b)
        a.publish()
        a.save()

        url = reverse('action-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}?behavior={1}".format(url, self.behavior.title_slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.action.id)

        # Clean up.
        a.delete()
        b.delete()

    def test_post_action_list(self):
        """Ensure this endpoint is read-only."""
        url = reverse('action-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_action_detail(self):
        url = reverse('action-detail', args=[self.action.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.action.id)

    def test_post_action_detail(self):
        """Ensure this endpoint is read-only."""
        url = reverse('action-detail', args=[self.action.id])
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestUserGoalAPI(APITestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(
            username="test",
            email="test@example.com",
        )
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            state='published'
        )
        self.goal = Goal.objects.create(
            title="Test Goal",
            subtitle="A subtitle",
            description="A Description",
            state='published'
        )
        self.goal.categories.add(self.category)

        self.ug = UserGoal.objects.create(
            user=self.user,
            goal=self.goal,
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(id=self.user.id).delete()
        Goal.objects.filter(id=self.goal.id).delete()
        Category.objects.filter(id=self.category.id).delete()
        UserGoal.objects.filter(id=self.ug.id).delete()

    def test_usergoal_list(self):
        """Ensure un-authenticated requests don't expose any results."""
        url = reverse('usergoal-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usergoal_list_authenticated(self):
        """Ensure authenticated requests DO expose results."""
        url = reverse('usergoal-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['user'], self.user.id)
        self.assertEqual(
            response.data['results'][0]['goal']['id'],
            self.goal.id
        )
        self.assertEqual(
            response.data['results'][0]['goal']['title'],
            self.goal.title
        )
        self.assertTrue(response.data['results'][0]['custom_triggers_allowed'])

    def test_post_usergoal_list_unathenticated(self):
        """Unauthenticated requests should not be allowed to post new UserGoals"""
        url = reverse('usergoal-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_usergoal_list_athenticated(self):
        """Authenticated users Should be able to create a UserGoal."""
        newgoal = Goal.objects.create(title="New", subtitle="New")

        url = reverse('usergoal-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {"goal": newgoal.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(UserGoal.objects.filter(user=self.user).count(), 2)

        # Clean up.
        newgoal.delete()

    def test_post_usergoal_list_multiple_authenticated(self):
        """POST should be allowed for authenticated users"""
        goal_a = Goal.objects.create(title="A", subtitle="New Goal A")
        goal_a.publish()
        goal_a.save()

        goal_b = Goal.objects.create(title="B", subtitle="New Goal B")
        goal_b.publish()
        goal_b.save()

        url = reverse('usergoal-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        post_data = [
            {'goal': goal_a.id},
            {'goal': goal_b.id}
        ]
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure our user is associated with the categories.
        self.assertEqual(self.user.usergoal_set.count(), 3)

        # clean up.
        goal_a.delete()
        goal_b.delete()

    def test_post_duplicate_usergoal_list(self):
        """Attempting to POST a duplicate UserGoal should return a 400."""
        url = reverse('usergoal-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        # Post an ID to which the user already has an association
        response = self.client.post(url, {'goal': self.ug.goal.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_usergoal_detail_unauthed(self):
        """Ensure unauthenticated users cannot view this endpoint."""
        url = reverse('usergoal-detail', args=[self.ug.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_usergoal_detail(self):
        """Ensure authenticated users can view this endpoint."""
        url = reverse('usergoal-detail', args=[self.ug.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_usergoal_detail_not_allowed(self):
        """Ensure POSTing to the detail endpoint is not allowed."""
        url = reverse('usergoal-detail', args=[self.ug.id])
        response = self.client.post(url, {'goal': 1})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {'goal': 1})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_usergoal_detail_not_allowed(self):
        """Ensure PUTing to the detail endpoint is not allowed."""
        url = reverse('usergoal-detail', args=[self.ug.id])
        response = self.client.put(url, {'goal': 1})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, {'goal': 1})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_usergoal_detail_unauthed(self):
        """Ensure unauthenticated users cannot delete."""
        url = reverse('usergoal-detail', args=[self.ug.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_usergoal_detail(self):
        """Ensure authenticated users can deelte."""
        url = reverse('usergoal-detail', args=[self.ug.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserGoal.objects.filter(id=self.ug.id).count(), 0)

    def test_delete_usergoal_multiple_unauthenticated(self):
        """Ensure unauthenticated users cannot delete UserGoal's"""
        other_goal = Goal.objects.create(title="Second Goal")
        other_ug = UserGoal.objects.create(user=self.user, goal=other_goal)

        url = reverse('usergoal-list')
        data = [
            {'usergoal': self.ug.id},
            {'usergoal': other_ug.id},
        ]

        response = self.client.delete(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Clean up.
        other_ug.delete()
        other_goal.delete()

    def test_delete_usercategory_multiple_authenticated(self):
        """Ensure that we can delete multiple UserCategory objects."""
        other_goal = Goal.objects.create(title="Second Goal")
        other_ug = UserGoal.objects.create(user=self.user, goal=other_goal)

        url = reverse('usergoal-list')
        data = [
            {'usergoal': self.ug.id},
            {'usergoal': other_ug.id},
        ]

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.delete(url, data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserGoal.objects.filter(id=other_ug.id).exists())

        # Clean up.
        other_goal.delete()


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestUserBehaviorAPI(APITestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(
            username="test",
            email="test@example.com",
        )
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            state='published'
        )
        self.goal = Goal.objects.create(
            title="Test Goal",
            subtitle="A subtitle",
            description="A Description",
            state='published'
        )
        self.goal.categories.add(self.category)

        self.behavior = Behavior.objects.create(
            title="Test Behavior",
            state='published'
        )
        self.behavior.goals.add(self.goal)
        self.behavior.save()

        self.ub = UserBehavior.objects.create(
            user=self.user,
            behavior=self.behavior,
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(id=self.user.id).delete()
        Goal.objects.filter(id=self.goal.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()
        UserBehavior.objects.filter(id=self.ub.id).delete()

    def test_userbehavior_list_unauthenticated(self):
        """Ensure un-authenticated requests don't expose any results."""
        url = reverse('userbehavior-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_userbehavior_list_authenticated(self):
        """Ensure authenticated requests DO expose results."""
        url = reverse('userbehavior-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        self.assertTrue(response.data['results'][0]['custom_triggers_allowed'])
        self.assertIn("user_categories", response.data['results'][0])
        self.assertIn("user_goals", response.data['results'][0])
        self.assertIn("user_actions", response.data['results'][0])
        self.assertIn("user_actions_count", response.data['results'][0])
        self.assertEqual(response.data['results'][0]['user'], self.user.id)
        self.assertEqual(
            response.data['results'][0]['behavior']['id'],
            self.behavior.id
        )
        self.assertEqual(
            response.data['results'][0]['behavior']['title'],
            self.behavior.title
        )

    def test_get_userbehavior_list_with_filters(self):
        # Test with goal id
        url = "{0}?goal={1}".format(reverse('userbehavior-list'), self.goal.id)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # Test with goal title_slug
        url = "{0}?goal={1}".format(
            reverse('userbehavior-list'),
            self.goal.title_slug
        )
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_post_userbehavior_list_unathenticated(self):
        """Unauthenticated requests should not be allowed to post"""
        url = reverse('userbehavior-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_userbehavior_list_athenticated(self):
        """Authenticated users Should be able to create a UserBehavior."""
        newbehavior = Behavior.objects.create(title="New")

        url = reverse('userbehavior-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {"behavior": newbehavior.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(UserBehavior.objects.filter(user=self.user).count(), 2)

        # Clean up.
        newbehavior.delete()

    def test_post_userbehavior_list_multiple_athenticated(self):
        """Authenticated users Should be able to create a multiple UserBehaviors."""
        behavior_a = Behavior.objects.create(title="New A")
        behavior_b = Behavior.objects.create(title="New B")

        url = reverse('userbehavior-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        data = [{"behavior": behavior_a.id}, {"behavior": behavior_b.id}]
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(UserBehavior.objects.filter(user=self.user).count(), 3)

        # Clean up.
        behavior_a.delete()
        behavior_b.delete()

    def test_post_duplicate_userbehavior_list(self):
        """Attempting to POST a duplicate UserBehavior should return a 400."""
        url = reverse('userbehavior-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        # Post an ID to which the user already has an association
        response = self.client.post(url, {'behavior': self.ub.behavior.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_userbehavior_detail_unauthed(self):
        """Ensure unauthenticated users cannot view this endpoint."""
        url = reverse('userbehavior-detail', args=[self.ub.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_userbehavior_detail(self):
        """Ensure authenticated users can view this endpoint."""
        url = reverse('userbehavior-detail', args=[self.ub.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_userbehavior_detail_not_allowed(self):
        """Ensure POSTing to the detail endpoint is not allowed."""
        url = reverse('userbehavior-detail', args=[self.ub.id])
        response = self.client.post(url, {'behavior': 1})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {'behavior': 1})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_userbehavior_detail_unauthenticated_not_allowed(self):
        """Ensure PUTing to the detail endpoint is not allowed."""
        url = reverse('userbehavior-detail', args=[self.ub.id])
        response = self.client.put(url, {'behavior': 1})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_userbehavior_detail_authenticated(self):
        """PUT requests should update a UserBehavior (sorta). While this is
        technically allowed, it doesn't really do much without providing
        a custom trigger information.

        Essentially, PUTing {user: <id>, behavior: <id>} should update, but
        wouldn't change any information.

        """
        url = reverse('userbehavior-detail', args=[self.ub.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        payload = {
            'user': self.user.id,
            'behavior': self.behavior.id,
        }
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_userbehavior_detail_authenticated_with_custom_trigger(self):
        """PUT requests containting custom trigger details, should create
        a custom trigger (if that field was previously null) for the
        UserBehavior.

        """
        url = reverse('userbehavior-detail', args=[self.ub.id])
        payload = {
            'custom_trigger_time': '9:30',
            'custom_trigger_rrule': 'RRULE:FREQ=WEEKLY;BYDAY=MO',
        }
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )

        # NOTE: user & action are required fields
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ensure the custom trigger was created.
        ub = UserBehavior.objects.get(pk=self.ub.id)
        self.assertIsNotNone(ub.custom_trigger)
        self.assertEqual(ub.get_custom_trigger_name(), ub.custom_trigger.name)
        self.assertEqual(
            ub.custom_trigger.recurrences_as_text(),
            "weekly, each Monday"
        )
        self.assertEqual(ub.custom_trigger.time, time(9, 30))

    def test_delete_userbehavior_detail_unauthed(self):
        """Ensure unauthenticated users cannot delete."""
        url = reverse('userbehavior-detail', args=[self.ub.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_userbehavior_detail(self):
        """Ensure authenticated users can deelte."""
        url = reverse('userbehavior-detail', args=[self.ub.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserBehavior.objects.filter(id=self.ub.id).count(), 0)

    def test_delete_userbehavior_multiple_unauthenticated(self):
        """Ensure unauthenticated users cannot delete UserBehavior's"""
        other_behavior = Behavior.objects.create(title="Second Behavior")
        other_ub = UserBehavior.objects.create(
            user=self.user,
            behavior=other_behavior
        )

        url = reverse('userbehavior-list')
        data = [
            {'userbehavior': self.ub.id},
            {'userbehavior': other_ub.id},
        ]

        response = self.client.delete(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Clean up.
        other_ub.delete()
        other_behavior.delete()

    def test_delete_usercategory_multiple_authenticated(self):
        """Ensure that we can delete multiple UserCategory objects."""
        other_behavior = Behavior.objects.create(title="Second Behavior")
        other_ub = UserBehavior.objects.create(
            user=self.user,
            behavior=other_behavior
        )

        url = reverse('userbehavior-list')
        data = [
            {'userbehavior': self.ub.id},
            {'userbehavior': other_ub.id},
        ]

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.delete(url, data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserBehavior.objects.filter(id=other_ub.id).exists())

        # Clean up.
        other_behavior.delete()


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestUserActionAPI(APITestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(
            username="test",
            email="test@example.com",
        )
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            state='published'
        )
        self.goal = Goal.objects.create(
            title="Test Goal",
            subtitle="A subtitle",
            description="A Description",
        )
        self.goal.categories.add(self.category)

        self.behavior = Behavior.objects.create(title="Test Action")
        self.behavior.publish()
        self.behavior.goals.add(self.goal)
        self.behavior.save()

        self.action = Action.objects.create(
            title="Test Action",
            behavior=self.behavior
        )
        self.action.publish()
        self.action.save()

        self.ua = UserAction.objects.create(
            user=self.user,
            action=self.action,
        )

    def tearDown(self):
        User = get_user_model()
        UserAction.objects.filter(id=self.ua.id).delete()
        User.objects.filter(id=self.user.id).delete()

        Goal.objects.filter(id=self.goal.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()
        Action.objects.filter(id=self.action.id).delete()

    def test_get_useraction_list_unauthenticated(self):
        """Ensure un-authenticated requests don't expose any results."""
        url = reverse('useraction-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_useraction_list_authenticated(self):
        """Ensure authenticated requests DO expose results."""
        url = reverse('useraction-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['user'], self.user.id)

        # Make some assertions about the data returned
        ua = response.data['results'][0]
        self.assertIn('id', ua)
        self.assertIn('user', ua)
        self.assertIn('created_on', ua)
        self.assertEqual(ua['user'], self.user.id)
        self.assertTrue(ua['custom_triggers_allowed'])

    def test_get_useraction_list_with_filters(self):
        # Test with goal id
        url = "{0}?goal={1}".format(reverse('useraction-list'), self.goal.id)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # Test with goal title_slug
        url = "{0}?goal={1}".format(
            reverse('useraction-list'),
            self.goal.title_slug
        )
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # Test with Behavior id
        url = "{0}?behavior={1}".format(
            reverse('useraction-list'),
            self.behavior.id
        )
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # Test with Behavior title_slug
        url = "{0}?behavior={1}".format(
            reverse('useraction-list'),
            self.behavior.title_slug
        )
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_get_useraction_list_filtered_on_today(self):
        # Test with goal id
        url = "{0}?today=1".format(reverse('useraction-list'))
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_post_useraction_list_unathenticated(self):
        """Unauthenticated requests should not be allowed to post"""
        url = reverse('useraction-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_useraction_list_athenticated(self):
        """Authenticated users should be able to create a UserAction."""
        newaction = Action.objects.create(title="New", behavior=self.behavior)

        url = reverse('useraction-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        post_data = {'action': newaction.id}
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserAction.objects.filter(user=self.user).count(), 2)

        ua = UserAction.objects.get(user=self.user, action__title="New")
        self.assertIsNone(ua.primary_goal)

        # Clean up.
        newaction.delete()

    def test_post_useraction_list_athenticated_including_primary_goal(self):
        """Authenticated users should be able to create a UserAction. This test
        also includes a primary goal with the POST request."""
        newaction = Action.objects.create(title="New2", behavior=self.behavior)

        url = reverse('useraction-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )

        post_data = {'action': newaction.id, 'primary_goal': self.goal.id}
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserAction.objects.filter(user=self.user).count(), 2)

        ua = UserAction.objects.get(user=self.user, action__title="New2")
        self.assertEqual(ua.primary_goal, self.goal)

        # Clean up.
        newaction.delete()

    def test_post_useraction_list_multiple_athenticated(self):
        """Authenticated users should be able to create multiple UserActions."""
        action_a = Action.objects.create(title="Action A", behavior=self.behavior)
        action_b = Action.objects.create(title="Action B", behavior=self.behavior)

        url = reverse('useraction-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        post_data = [{"action": action_a.id}, {"action": action_b.id}]
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserAction.objects.filter(user=self.user).count(), 3)

        ua = UserAction.objects.get(user=self.user, action__id=action_a.id)
        self.assertIsNone(ua.primary_goal)
        ua = UserAction.objects.get(user=self.user, action__id=action_b.id)
        self.assertIsNone(ua.primary_goal)

        # Clean up.
        action_a.delete()
        action_b.delete()

    def test_post_useraction_list_multiple_athenticated_with_primary_goal(self):
        """Authenticated users should be able to create multiple UserActions AND
        include a primary goal with each."""
        action_a = Action.objects.create(title="Action A", behavior=self.behavior)
        action_b = Action.objects.create(title="Action B", behavior=self.behavior)

        url = reverse('useraction-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        post_data = [
            {"action": action_a.id, 'primary_goal': self.goal.id},
            {"action": action_b.id, 'primary_goal': self.goal.id},
        ]
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserAction.objects.filter(user=self.user).count(), 3)

        ua = UserAction.objects.get(user=self.user, action__id=action_a.id)
        self.assertEqual(ua.primary_goal, self.goal)
        ua = UserAction.objects.get(user=self.user, action__id=action_b.id)
        self.assertEqual(ua.primary_goal, self.goal)

        # Clean up.
        action_a.delete()
        action_b.delete()

    def test_post_duplicate_useraction_list(self):
        """Attempting to POST a duplicate UserAction should return a 400."""
        url = reverse('useraction-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        # Post an ID to which the user already has an association
        response = self.client.post(url, {'action': self.ua.action.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_useraction_detail_unauthenticated(self):
        """Ensure unauthenticated users cannot view this endpoint."""
        url = reverse('useraction-detail', args=[self.ua.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_useraction_detail_authenticated(self):
        """Ensure authenticated users can view this endpoint."""
        url = reverse('useraction-detail', args=[self.ua.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_useraction_detail_not_allowed(self):
        """Ensure POSTing to the detail endpoint is not allowed."""
        url = reverse('useraction-detail', args=[self.ua.id])
        response = self.client.post(url, {'action': 1})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {'action': 1})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_useraction_detail_unauthenticated_not_allowed(self):
        """Ensure PUTing to the detail endpoint is not allowed for
        unauthenticated users."""
        url = reverse('useraction-detail', args=[self.ua.id])
        response = self.client.put(url, {'action': 1})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_useraction_detail_authenticated_with_no_data(self):
        """PUT requests should update a UserAction (sorta). While this is
        technically allowed, it doesn't really do much without providing
        a custom trigger information.

        Essentially, PUTing {user: <id>, action: <id>} should update, but
        wouldn't change any information.

        """
        url = reverse('useraction-detail', args=[self.ua.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        # NOTE: user & action are required fields
        payload = {'user': self.user.id, 'action': self.action.id}
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ensure the trigger was created/updated.
        ua = UserAction.objects.get(pk=self.ua.id)
        self.assertIsNone(ua.custom_trigger)

    def test_put_useraction_detail_authenticated_with_empty_data(self):
        """PUT requests should update a UserAction when blank data is provided
        for the custom trigger; Doing this will essentially deactivate the
        trigger.

        """
        url = reverse('useraction-detail', args=[self.ua.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        # NOTE: user & action are required fields
        payload = {
            'user': self.user.id,
            'action': self.action.id,
            'custom_trigger_time': '',
            'custom_trigger_date': '',
            'custom_trigger_rrule': '',
        }
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ensure the trigger was created/updated.
        ua = UserAction.objects.get(pk=self.ua.id)
        expected_name = ua.get_custom_trigger_name()
        self.assertEqual(ua.custom_trigger.name, expected_name)
        self.assertIsNone(ua.custom_trigger.trigger_date)
        self.assertIsNone(ua.custom_trigger.time)
        self.assertIsNone(ua.custom_trigger.recurrences)

    def test_put_useraction_detail_authenticated_with_custom_trigger(self):
        """PUT requests containting custom trigger details, should create
        a custom trigger (if that field was previously null) for the UserAction.

        """
        url = reverse('useraction-detail', args=[self.ua.id])
        payload = {
            'custom_trigger_date': '2222-12-25',
            'custom_trigger_time': '9:30',
            'custom_trigger_rrule': 'RRULE:FREQ=WEEKLY;BYDAY=MO',
        }
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )

        # NOTE: user & action are required fields
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ensure the user action was created.
        ua = UserAction.objects.get(pk=self.ua.id)
        self.assertIsNotNone(ua.custom_trigger)
        self.assertEqual(ua.get_custom_trigger_name(), ua.custom_trigger.name)
        self.assertEqual(
            ua.custom_trigger.recurrences_as_text(),
            "weekly, each Monday"
        )
        self.assertEqual(ua.custom_trigger.time, time(9, 30))
        self.assertEqual(ua.custom_trigger.trigger_date, date(2222, 12, 25))

    def test_put_useraction_custom_trigger_udpates(self):
        """When we have an existing custom trigger, putting new values should
        update it."""

        # Create a Custom trigger for our UserAction
        custom_trigger = Trigger.objects.create_for_user(
            user=self.ua.user,
            name="custom trigger for useraction-{0}".format(self.ua.id),
            time=time(11, 30),
            date=date(2000, 1, 2),
            rrule="RRULE:FREQ=DAILY"
        )

        url = reverse('useraction-detail', args=[self.ua.id])
        payload = {
            'custom_trigger_date': '2222-12-25',
            'custom_trigger_time': '9:30',
            'custom_trigger_rrule': 'RRULE:FREQ=WEEKLY;BYDAY=MO',
        }
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )

        # NOTE: user & action are required fields
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that the Trigger got updated.
        ua = UserAction.objects.get(pk=self.ua.id)
        self.assertEqual(ua.custom_trigger.id, custom_trigger.id)
        expected_name = "custom trigger for useraction-{0}".format(ua.id)
        self.assertEqual(ua.custom_trigger.name, expected_name)
        self.assertEqual(
            ua.custom_trigger.recurrences_as_text(),
            "weekly, each Monday"
        )
        self.assertEqual(ua.custom_trigger.time, time(9, 30))
        self.assertEqual(ua.custom_trigger.trigger_date, date(2222, 12, 25))

        # clean up
        Trigger.objects.filter(id=custom_trigger.id).delete()

    def test_put_useraction_custom_trigger_disable(self):
        """When we have an existing custom trigger, PUTing blank values for the
        trigger details should disable it."""

        # Create a Custom trigger for our UserAction
        custom_trigger = Trigger.objects.create_for_user(
            user=self.ua.user,
            name="custom trigger for useraction-{0}".format(self.ua.id),
            time=time(11, 30),
            date=date(2000, 1, 2),
            rrule="RRULE:FREQ=DAILY"
        )

        url = reverse('useraction-detail', args=[self.ua.id])
        payload = {
            'custom_trigger_date': '',
            'custom_trigger_time': '',
            'custom_trigger_rrule': '',
        }
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )

        # NOTE: user & action are required fields
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that the Trigger got updated.
        ua = UserAction.objects.get(pk=self.ua.id)
        self.assertEqual(ua.custom_trigger.id, custom_trigger.id)
        expected_name = "custom trigger for useraction-{0}".format(ua.id)
        self.assertEqual(ua.custom_trigger.name, expected_name)
        self.assertIsNone(ua.custom_trigger.recurrences)
        self.assertIsNone(ua.custom_trigger.time)
        self.assertIsNone(ua.custom_trigger.trigger_date)

        # clean up
        Trigger.objects.filter(id=custom_trigger.id).delete()

    def test_delete_useraction_detail_unauthenticated(self):
        """Ensure unauthenticated users cannot delete."""
        url = reverse('useraction-detail', args=[self.ua.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_useraction_detail_authenticated(self):
        """Ensure authenticated users can deelte."""
        url = reverse('useraction-detail', args=[self.ua.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserAction.objects.filter(id=self.ua.id).count(), 0)

    def test_delete_useraction_multiple_unauthenticated(self):
        """Ensure unauthenticated users cannot delete UserAction's"""
        other_action = Action.objects.create(
            title="Second Action",
            behavior=self.behavior
        )
        other_ua = UserAction.objects.create(user=self.user, action=other_action)

        url = reverse('useraction-list')
        data = [
            {'useraction': self.ua.id},
            {'useraction': other_ua.id},
        ]

        response = self.client.delete(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Clean up.
        other_ua.delete()
        other_action.delete()

    def test_delete_usercategory_multiple_authenticated(self):
        """Ensure that we can delete multiple UserCategory objects."""
        other_action = Action.objects.create(
            title="Second Action",
            behavior=self.behavior
        )
        other_ua = UserAction.objects.create(user=self.user, action=other_action)

        url = reverse('useraction-list')
        data = [
            {'useraction': self.ua.id},
            {'useraction': other_ua.id},
        ]

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.delete(url, data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserAction.objects.filter(id=other_ua.id).exists())

        # Clean up.
        other_action.delete()

    def test_user_completed_action(self):
        url = reverse('useraction-complete', args=[self.ua.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        # First with no body (should set the state to completed)
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        uca = UserCompletedAction.objects.get(user=self.user, useraction=self.ua)
        self.assertTrue(uca.completed)

        # Now set it's state to 'dismissed'
        response = self.client.post(url, {'state': 'dismissed'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        uca = UserCompletedAction.objects.get(user=self.user, useraction=self.ua)
        self.assertTrue(uca.dismissed)

        # Now set it's state to 'snoozed'
        response = self.client.post(url, {'state': 'snoozed'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        uca = UserCompletedAction.objects.get(user=self.user, useraction=self.ua)
        self.assertTrue(uca.snoozed)

        # Now set it's state to 'uncompleted'
        response = self.client.post(url, {'state': 'uncompleted'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        uca = UserCompletedAction.objects.get(user=self.user, useraction=self.ua)
        self.assertTrue(uca.uncompleted)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestUserCategoryAPI(APITestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(
            username="test",
            email="test@example.com",
        )
        self.category = Category.objects.create(
            title="Test Category",
            order=1,
            state='published'
        )
        # Assign a Category to the User
        self.uc = UserCategory.objects.create(user=self.user, category=self.category)

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(id=self.user.id).delete()
        Category.objects.filter(id=self.category.id).delete()
        UserCategory.objects.filter(id=self.uc.id).delete()

    def test_get_usercategory_list_unauthenticated(self):
        """Ensure un-authenticated requests don't expose any results."""
        url = reverse('usercategory-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_usercategory_list_authenticated(self):
        """Ensure authenticated requests DO expose results."""
        url = reverse('usercategory-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # check the fields of a result object.
        self.assertIn("id", response.data['results'][0])
        self.assertIn("category", response.data['results'][0])
        self.assertIn("custom_triggers_allowed", response.data['results'][0])
        self.assertIn("order", response.data['results'][0]['category'])
        self.assertIn("title", response.data['results'][0]['category'])
        self.assertIn("description", response.data['results'][0]['category'])
        self.assertIn("icon_url", response.data['results'][0]['category'])
        self.assertIn("image_url", response.data['results'][0]['category'])

        self.assertEqual(
            response.data['results'][0]['id'],
            self.uc.id
        )
        self.assertEqual(
            response.data['results'][0]['category']['id'],
            self.category.id
        )
        self.assertEqual(
            response.data['results'][0]['category']['title'],
            self.category.title
        )
        self.assertTrue(response.data['results'][0]['custom_triggers_allowed'])
        # TODO: it'd be nice if these fields actually had data.
        self.assertEqual(response.data['results'][0]['category']['image_url'], None)
        self.assertEqual(response.data['results'][0]['category']['icon_url'], None)

    def test_post_usercategory_list_unauthenticated(self):
        """POST should not be allowed for unauthenticated users"""
        url = reverse('usercategory-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_usercategory_list_authenticated(self):
        """POST should be allowed for authenticated users"""
        newcat = Category.objects.create(order=2, title="NEW")

        url = reverse('usercategory-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {"category": newcat.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure our user has two categories.
        self.assertEqual(self.user.usercategory_set.count(), 2)

        # clean up.
        newcat.delete()

    def test_post_usercategory_list_multiple_authenticated(self):
        """POST should be allowed for authenticated users"""
        cat_a = Category.objects.create(order=2, title="A")
        cat_b = Category.objects.create(order=3, title="B")

        url = reverse('usercategory-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        post_data = [
            {'category': cat_a.id},
            {'category': cat_b.id}
        ]
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure our user is associated with the categories.
        self.assertEqual(self.user.usercategory_set.count(), 3)

        # clean up.
        cat_a.delete()
        cat_b.delete()

    def test_post_duplicate_usercategory_list(self):
        """Attempting to POST a duplicate UserCategory should return a 400."""
        url = reverse('usercategory-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        # Post an ID to which the user already has an association
        response = self.client.post(url, {'category': self.uc.category.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_usercategory_detail_unauthenticated(self):
        """Ensure unauthenticated users cannot view this endpoint."""
        url = reverse('usercategory-detail', args=[self.uc.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_usercategory_detail_authenticated(self):
        """Ensure authenticated users can view this endpoint."""
        url = reverse('usercategory-detail', args=[self.uc.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_usercategory_detail_not_allowed(self):
        """Ensure POSTing to the detail endpoint is not allowed."""
        url = reverse('usercategory-detail', args=[self.uc.id])
        response = self.client.post(url, {'category': 1})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {'category': 1})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_usercategory_detail_not_allowed(self):
        """Ensure PUTing to the detail endpoint is not allowed."""
        url = reverse('usercategory-detail', args=[self.uc.id])
        response = self.client.put(url, {'category': 1})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, {'category': 1})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_usercategory_detail_unauthenticated(self):
        """Ensure unauthenticated users cannot delete."""
        url = reverse('usercategory-detail', args=[self.uc.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_usercategory_detail_authenticated(self):
        """Ensure authenticated users can deelte."""
        url = reverse('usercategory-detail', args=[self.uc.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserCategory.objects.filter(id=self.uc.id).count(), 0)

    def test_delete_usercategory_multiple_unauthenticated(self):
        """Ensure unauthenticated users cannot delete UserCategory's"""
        other_cat = Category.objects.create(title="Second Category", order=2)
        other_uc = UserCategory.objects.create(user=self.user, category=other_cat)

        url = reverse('usercategory-list')
        uc_data = [
            {'usercategory': self.uc.id},
            {'usercategory': other_uc.id},
        ]

        response = self.client.delete(url, uc_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Clean up.
        other_uc.delete()
        other_cat.delete()

    def test_delete_usercategory_multiple_authenticated(self):
        """Ensure that we can delete multiple UserCategory objects."""
        other_cat = Category.objects.create(title="Second Category", order=2)
        other_uc = UserCategory.objects.create(user=self.user, category=other_cat)

        url = reverse('usercategory-list')
        uc_data = [
            {'usercategory': self.uc.id},
            {'usercategory': other_uc.id},
        ]

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.delete(url, uc_data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserCategory.objects.filter(id=other_uc.id).exists())

        # Clean up.
        other_cat.delete()


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestPackageEnrollmentAPI(APITestCase):

    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create(
            username="admin",
            email="admin@example.com",
        )
        self.user = User.objects.create(
            username="test",
            email="test@example.com",
        )
        self.category = Category.objects.create(
            order=1,
            title="Test Cat",
            created_by=self.admin,
            consent_summary="Summary",
            consent_more="More",
            packaged_content=True,
        )
        self.category.contributors.add(self.admin)
        self.category.publish()
        self.category.save()

        self.goal = Goal.objects.create(title="Test Goal")
        self.goal.categories.add(self.category)
        self.goal.publish()

        self.package = PackageEnrollment.objects.create(
            user=self.user,
            category=self.category,
            enrolled_by=self.admin,
        )
        self.package.goals.add(self.goal)

        self.url = reverse('packageenrollment-list')
        self.detail_url = reverse(
            'packageenrollment-detail',
            args=[self.package.id]
        )
        self.payload = {'accepted': True}

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(id__in=[self.user.id, self.admin.id]).delete()
        Category.objects.filter(id=self.category.id).delete()
        Goal.objects.filter(id=self.goal.id).delete()

    def test_get_list_unauthenticated(self):
        """Ensure un-authenticated requests don't expose any results."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_list_authenticated(self):
        """Ensure authenticated requests DO expose results."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_post_list_unauthenticated(self):
        """Creating objects via the api is not allowed."""
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_list_authenticated(self):
        """Creating objects via the api is not allowed."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_detail_unauthenticated(self):
        """Ensure un-authenticated requests don't expose any results."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_detail_authenticated(self):
        """Ensure authenticated requests DO expose results."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['id'], self.package.id)
        self.assertEqual(response.data['user'], self.user.id)
        self.assertEqual(response.data['accepted'], False)

        # NOTE: the api is supposed to format in ISO format, but it differs
        # slightly, becuase the +00:00 is omitted.
        updated = self.package.updated_on.strftime(DRF_DT_FORMAT)
        self.assertEqual(response.data['updated_on'], updated)
        enrolled = self.package.enrolled_on.strftime(DRF_DT_FORMAT)
        self.assertEqual(response.data['enrolled_on'], enrolled)
        self.assertEqual(response.data['category']['id'], self.category.id)
        self.assertEqual(response.data['goals'][0]['id'], self.goal.id)

    def test_post_detail_should_fail(self):
        """POSTing to the detail endpoint should fail unless we're accepting
        an enrollment."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        # post some invalid data
        response = self.client.post(self.detail_url, {'category': 123})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_detail_to_accept(self):
        """POSTing to the detail endpoint can be used to accept an enrollment"""
        package = PackageEnrollment.objects.create(
            user=self.user,
            category=self.category,
            enrolled_by=self.admin,
        )
        url = reverse('packageenrollment-detail', args=[package.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {'accepted': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        package = PackageEnrollment.objects.get(pk=package.id)
        self.assertTrue(package.accepted)

    def test_post_packageenrollment_accept(self):
        """POSTing to the packageenrollment-accept detail_route should accept
        a PackageEnrollment."""
        package = PackageEnrollment.objects.create(
            user=self.user,
            category=self.category,
            enrolled_by=self.admin,
        )
        url = reverse('packageenrollment-accept', args=[package.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {'accepted': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        package = PackageEnrollment.objects.get(pk=package.id)
        self.assertTrue(package.accepted)

    def test_put_detail_unauthenticated(self):
        """Ensure updates are not allowed when unauthenticated."""
        response = self.client.put(self.detail_url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_detail_updates_accept(self):
        """Updating PackageEnrollment should work when authenticated."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(self.detail_url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        package = PackageEnrollment.objects.get(pk=self.package.id)
        self.assertTrue(package.accepted)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestCustomGoalAPI(APITestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(
            username="test",
            email="test@example.com",
        )
        self.customgoal = CustomGoal.objects.create(
            user=self.user,
            title="Existing Custom Goal"
        )

    def test_customgoal_list(self):
        """Ensure un-authenticated requests don't expose any results."""
        url = reverse('customgoal-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customgoal_list_authenticated(self):
        """Ensure authenticated requests DO expose results."""
        url = reverse('customgoal-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertTrue(len(response.data['results']) > 0)

        result = response.data['results'][0]
        self.assertEqual(result['user'], self.user.id)
        self.assertEqual(result['id'], self.customgoal.id)
        self.assertEqual(result['title'], self.customgoal.title)
        self.assertEqual(result['title_slug'], self.customgoal.title_slug)
        self.assertEqual(result['object_type'], "customgoal")
        self.assertTrue('updated_on' in result)
        self.assertTrue('created_on' in result)

    def test_post_customgoal_list_unathenticated(self):
        """Unauthenticated requests should not be allowed to post new
        CustomGoals"""
        url = reverse('customgoal-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_customgoal_list_athenticated(self):
        """Authenticated users should be able to create a CustomGoal."""
        url = reverse('customgoal-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {"title": "New Custom Goal"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomGoal.objects.filter(user=self.user).count(), 2)

    def test_get_customgoal_detail_unauthed(self):
        """Ensure unauthenticated users cannot view this endpoint."""
        url = reverse('customgoal-detail', args=[self.customgoal.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_customgoal_detail(self):
        """Ensure authenticated users can view this endpoint."""
        url = reverse('customgoal-detail', args=[self.customgoal.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_customgoal_detail_not_allowed(self):
        """Ensure POSTing to the detail endpoint is not allowed."""
        url = reverse('customgoal-detail', args=[self.customgoal.id])
        response = self.client.post(url, {'title': 'foo'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {'title': 'foo'})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_customgoal_detail_unauthenticated(self):
        """Ensure PUTing to the detail endpoint is not allowed."""
        url = reverse('customgoal-detail', args=[self.customgoal.id])
        response = self.client.put(url, {'title': 'Altered'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_customgoal_detail(self):
        """Ensure PUTing to the detail endpoint updates."""
        url = reverse('customgoal-detail', args=[self.customgoal.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, {'title': 'Altered'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cg = CustomGoal.objects.get(pk=self.customgoal.id)
        self.assertEqual(cg.title, 'Altered')

    def test_delete_customgoal_detail_unauthed(self):
        """Ensure unauthenticated users cannot delete."""
        url = reverse('customgoal-detail', args=[self.customgoal.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_customgoal_detail(self):
        """Ensure authenticated users can delete."""
        cg = CustomGoal.objects.create(user=self.user, title="DELETE")
        url = reverse('customgoal-detail', args=[cg.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CustomGoal.objects.filter(title='DELETE').exists())


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestCustomActionAPI(APITestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(
            username="test",
            email="test@example.com",
        )
        self.customgoal = CustomGoal.objects.create(
            user=self.user,
            title="Existing Custom Goal"
        )
        self.customaction = CustomAction.objects.create(
            user=self.user,
            customgoal=self.customgoal,
            title="Existing Custom Action",
            notification_text='Do it'
        )

        # POST payload data
        self.payload = {
            'title': 'Existing Custom THING',
            'notification_text': 'Keep at it',
            'customgoal': self.customgoal.id,
        }

    def test_customaction_list(self):
        """Ensure un-authenticated requests don't expose any results."""
        url = reverse('customaction-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customaction_list_authenticated(self):
        """Ensure authenticated requests DO expose results."""
        url = reverse('customaction-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertTrue(len(response.data['results']) > 0)

        result = response.data['results'][0]
        self.assertEqual(result['user'], self.user.id)
        self.assertEqual(result['id'], self.customaction.id)
        self.assertEqual(result['title'], self.customaction.title)
        self.assertEqual(result['title_slug'], self.customaction.title_slug)
        self.assertEqual(result['customgoal'], self.customgoal.id)
        self.assertEqual(result['notification_text'], 'Do it'),
        self.assertEqual(result['object_type'], "customaction")
        self.assertTrue('next_reminder' in result)
        self.assertTrue('updated_on' in result)
        self.assertTrue('created_on' in result)

    def test_post_customaction_list_unathenticated(self):
        """Unauthenticated requests should not be allowed to post new
        CustomActions"""
        url = reverse('customaction-list')
        response = self.client.post(url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_customaction_list_athenticated(self):
        """Authenticated users should be able to create a CustomAction."""
        url = reverse('customaction-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomAction.objects.filter(user=self.user).count(), 2)

    def test_get_customaction_detail_unauthed(self):
        """Ensure unauthenticated users cannot view this endpoint."""
        url = reverse('customaction-detail', args=[self.customaction.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_customaction_detail(self):
        """Ensure authenticated users can view this endpoint."""
        url = reverse('customaction-detail', args=[self.customaction.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_customaction_detail_not_allowed(self):
        """Ensure POSTing to the detail endpoint is not allowed."""
        url = reverse('customaction-detail', args=[self.customaction.id])
        response = self.client.post(url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Even if you're authenticated
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_customaction_detail_unauthenticated(self):
        """Ensure PUTing to the detail endpoint is not allowed."""
        url = reverse('customaction-detail', args=[self.customaction.id])
        response = self.client.put(url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_customaction_detail(self):
        """Ensure PUTing to the detail endpoint updates."""
        url = reverse('customaction-detail', args=[self.customaction.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        payload = {
            'title': 'Altered',
            'notification_text': self.customaction.notification_text,
            'customgoal': self.customgoal.id,
        }
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ca = CustomAction.objects.get(pk=self.customaction.id)
        self.assertEqual(ca.title, 'Altered')

    def test_delete_customaction_detail_unauthed(self):
        """Ensure unauthenticated users cannot delete."""
        url = reverse('customaction-detail', args=[self.customaction.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_customaction_detail(self):
        """Ensure authenticated users can delete."""
        ca = CustomAction.objects.create(
            user=self.user,
            title="DELETE",
            customgoal=self.customgoal
        )
        url = reverse('customaction-detail', args=[ca.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CustomAction.objects.filter(title='DELETE').exists())

    def test_get_complete_unathenticated(self):
        url = reverse('customaction-complete', args=[self.customaction.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_complete_unathenticated(self):
        url = reverse('customaction-complete', args=[self.customaction.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_complete(self):
        """POSTing to the complete url should crate an UserCompletedCustomAction
        object for a user."""
        # We shouldn't have any just yet.
        qs = UserCompletedCustomAction.objects.filter(user=self.user)
        self.assertFalse(qs.exists())

        url = reverse('customaction-complete', args=[self.customaction.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {'state': 'completed'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        qs = UserCompletedCustomAction.objects.filter(user=self.user)
        self.assertTrue(qs.exists())

        obj = qs.get(customaction=self.customaction)
        self.assertEqual(obj.state, "completed")

    def test_post_feedback(self):
        """POSTing to the feedback url should crate an CustomActionFeedback
        object for a user."""
        # We shouldn't have any feedback objects just yet.
        qs = CustomActionFeedback.objects.filter(user=self.user)
        self.assertFalse(qs.exists())

        url = reverse('customaction-feedback', args=[self.customaction.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {'text': 'I did it'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        qs = CustomActionFeedback.objects.filter(user=self.user)
        self.assertTrue(qs.exists())

        obj = qs.get(customaction=self.customaction)
        self.assertEqual(obj.text, "I did it")

    def test_post_feedback_text_is_required(self):
        """POSTing to the feedback url should crate an CustomActionFeedback
        object for a user."""
        url = reverse('customaction-feedback', args=[self.customaction.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {'text': ''})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_detail_authenticated_with_empty_data(self):
        """PUT requests should update a CustomAction when blank data is provided
        for the custom trigger; Doing this will essentially deactivate the
        trigger.

        """
        url = reverse('customaction-detail', args=[self.customaction.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        # NOTE: user & action are required fields
        payload = {
            'title': "Updated Title",
            'notification_text': 'A notification',
            'customgoal': self.customgoal.id,
            'custom_trigger_time': '',
            'custom_trigger_date': '',
            'custom_trigger_rrule': '',
        }
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ensure the trigger was created/updated.
        ca = CustomAction.objects.get(pk=self.customaction.id)
        self.assertIsNone(ca.custom_trigger.trigger_date)
        self.assertIsNone(ca.custom_trigger.time)
        self.assertIsNone(ca.custom_trigger.recurrences)

    def test_put_detail_authenticated_with_custom_trigger(self):
        """PUT requests containting custom trigger details, should create
        a custom trigger (if that field was previously null) for the CustomAction.

        """
        url = reverse('customaction-detail', args=[self.customaction.id])
        payload = {
            'title': "Updated Title",
            'notification_text': 'A notification',
            'customgoal': self.customgoal.id,
            'custom_trigger_date': '2222-12-25',
            'custom_trigger_time': '9:30',
            'custom_trigger_rrule': 'RRULE:FREQ=WEEKLY;BYDAY=MO',
        }
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ensure it was updated
        ca = CustomAction.objects.get(pk=self.customaction.id)
        self.assertIsNotNone(ca.custom_trigger)
        self.assertEqual(
            ca.custom_trigger.recurrences_as_text(),
            "weekly, each Monday"
        )
        self.assertEqual(ca.custom_trigger.time, time(9, 30))
        self.assertEqual(ca.custom_trigger.trigger_date, date(2222, 12, 25))

    def test_put_custom_trigger_udpates(self):
        """When we have an existing custom trigger, putting new values should
        update it."""

        # Create a Custom trigger for our CustomAction
        custom_trigger = Trigger.objects.create_for_user(
            user=self.customaction.user,
            name="custom trigger for customaction-{0}".format(self.customaction.id),
            time=time(11, 30),
            date=date(2000, 1, 2),
            rrule="RRULE:FREQ=DAILY"
        )
        self.customaction.custom_trigger = custom_trigger
        self.customaction.save()

        url = reverse('customaction-detail', args=[self.customaction.id])
        payload = {
            'title': "Updated Title",
            'notification_text': 'A notification',
            'customgoal': self.customgoal.id,
            'custom_trigger_date': '2222-12-25',
            'custom_trigger_time': '9:30',
            'custom_trigger_rrule': 'RRULE:FREQ=WEEKLY;BYDAY=MO',
        }
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that the Trigger got updated.
        ca = CustomAction.objects.get(pk=self.customaction.id)
        self.assertEqual(ca.custom_trigger.id, custom_trigger.id)
        self.assertEqual(
            ca.custom_trigger.recurrences_as_text(),
            "weekly, each Monday"
        )
        self.assertEqual(ca.custom_trigger.time, time(9, 30))
        self.assertEqual(ca.custom_trigger.trigger_date, date(2222, 12, 25))

        # clean up
        Trigger.objects.filter(id=custom_trigger.id).delete()

    def test_put_customaction_custom_trigger_disable(self):
        """When we have an existing custom trigger, PUTing blank values for the
        trigger details should disable it."""

        # Create a Custom trigger for our CustomAction
        custom_trigger = Trigger.objects.create_for_user(
            user=self.customaction.user,
            name="custom trigger for customaction-{0}".format(self.customaction.id),
            time=time(11, 30),
            date=date(2000, 1, 2),
            rrule="RRULE:FREQ=DAILY"
        )
        self.customaction.custom_trigger = custom_trigger
        self.customaction.save()

        url = reverse('customaction-detail', args=[self.customaction.id])
        payload = {
            'title': "Updated Title",
            'notification_text': 'A notification',
            'customgoal': self.customgoal.id,
            'custom_trigger_date': '',
            'custom_trigger_time': '',
            'custom_trigger_rrule': '',
        }
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that the Trigger got updated.
        ca = CustomAction.objects.get(pk=self.customaction.id)
        self.assertEqual(ca.custom_trigger.id, custom_trigger.id)
        self.assertIsNone(ca.custom_trigger.recurrences)
        self.assertIsNone(ca.custom_trigger.time)
        self.assertIsNone(ca.custom_trigger.trigger_date)

        # clean up
        Trigger.objects.filter(id=custom_trigger.id).delete()
