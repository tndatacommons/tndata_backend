from datetime import date, time, timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import override_settings
from django.utils import timezone

from model_mommy import mommy
from rest_framework import status
from rest_framework.test import APITestCase
from utils.user_utils import tzdt

from .. models import (
    Action,
    Behavior,
    Category,
    CustomAction,
    CustomActionFeedback,
    CustomGoal,
    DailyProgress,
    Goal,
    Organization,
    PackageEnrollment,
    Program,
    Trigger,
    UserGoal,
    UserBehavior,
    UserCategory,
    UserAction,
    UserCompletedAction,
    UserCompletedCustomAction,
)
from .. permissions import get_or_create_content_authors


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


class V2APITestCase(APITestCase):
    """A parent class for the following test case that reverses a url and
    appends `?version=2`.

    """
    def get_url(self, name, args=None):
        return reverse(name, args=args) + '?version=2'


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestCategoryAPI(V2APITestCase):

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
        url = self.get_url('category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        c = response.data['results'][0]
        self.assertEqual(c['id'], self.category.id)
        self.assertEqual(c['description'], self.category.description)
        self.assertEqual(c['html_description'], self.category.rendered_description)
        self.assertEqual(c['title'], self.category.title)
        self.assertEqual(c['icon_url'], self.category.get_absolute_icon())
        self.assertEqual(c['image_url'], self.category.get_absolute_image())
        self.assertFalse(c['packaged_content'])

    def test_get_category_detail(self):
        """Test the Detail endpoint for regular, published categories"""
        url = self.get_url('category-detail', args=[self.category.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.category.id)

    def test_get_category_detail_package(self):
        """Test the detail endpoint for packages. Should not be exposed
        for unauthenticated users, but *should* be exposed if the user has
        been enrolled in the package.
        """
        cat = Category.objects.create(order=2, title='P', packaged_content=True)
        url = self.get_url('category-detail', args=[cat.id])

        # Regular requests to this should yield a 404
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # when the user is associated with the package, we should get a 200
        User = get_user_model()
        user = User.objects.create(username="a", email="a@b.co")
        uc = UserCategory.objects.create(user=user, category=cat)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Clean up
        uc.delete()
        cat.delete()
        user.delete()

    def test_post_category_list(self):
        """Ensure this endpoint is read-only."""
        url = self.get_url('category-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_post_category_detail(self):
        """Ensure this endpoint is read-only."""
        url = self.get_url('category-detail', args=[self.category.id])
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_category_list_when_user_has_packages(self):
        """Ensure the user sees categories (packages) they've selected, but NOT
        packages they haven't selected."""
        # when the user is associated with the package, we should get a 200
        User = get_user_model()
        user = User.objects.create(username="a", email="a@b.co")

        # Create additional categories / packages.
        pkg1 = Category.objects.create(order=2, title="P1", packaged_content=True)
        pkg2 = Category.objects.create(order=3, title="P2", packaged_content=True)
        for pkg in [pkg1, pkg2]:
            pkg.publish()
            pkg.save()
        pkg1.enroll(user)  # User is ONLY enrolled in P1

        # Make an authenticated request
        url = self.get_url('category-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        cats = sorted([c['title'] for c in response.data['results']])
        self.assertEqual(cats, ['P1', 'Test Category'])

    def test_category_list_when_user_in_program(self):
        """Ensure the user sees categories from a Program in which they're
        enrolled, but NOT categories that have been hidden from their Org."""

        # when the user is associated with the package, we should get a 200
        User = get_user_model()
        user = User.objects.create(username="a", email="a@b.co")

        # Create some Orgs & Programs
        org1 = mommy.make(Organization, name="O1")
        prog1 = mommy.make(Program, name="P1", organization=org1)
        org2 = mommy.make(Organization, name="O2")
        prog2 = mommy.make(Program, name="P2", organization=org2)

        # Create additional categories, and add the user to Org/Prog 1
        cat1 = Category.objects.create(order=2, title="C1")
        cat1.organizations.add(org1)
        cat1.hidden_from_organizations.add(org2)
        prog1.categories.add(cat1)

        cat2 = Category.objects.create(order=3, title="C2")
        cat2.organizations.add(org2)
        cat2.hidden_from_organizations.add(org1)
        prog2.categories.add(cat2)
        for cat in [cat1, cat2]:
            cat.publish()
            cat.save()

        cat1.enroll(user)  # User is ONLY enrolled in P1
        org1.members.add(user)
        prog1.members.add(user)

        # Make an authenticated request
        url = self.get_url('category-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        cats = sorted([c['title'] for c in response.data['results']])
        self.assertEqual(cats, ['C1', 'Test Category'])


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestGoalAPI(V2APITestCase):

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
        url = self.get_url('goal-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        obj = response.data['results'][0]
        self.assertEqual(obj['id'], self.goal.id)
        self.assertEqual(obj['title'], self.goal.title)
        self.assertEqual(obj['description'], self.goal.description)
        self.assertEqual(obj['html_description'], self.goal.rendered_description)
        self.assertIn('categories', obj)

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

        url = self.get_url('goal-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # Our other goal is here

        # Check the filtered result
        url = "{0}&category={1}".format(url, self.category.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.goal.id)

        # Clean up.
        g.delete()

    def test_post_goal_list(self):
        """Ensure this endpoint is read-only."""
        url = self.get_url('goal-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_goal_detail(self):
        url = self.get_url('goal-detail', args=[self.goal.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.goal.id)

    def test_post_goal_detail(self):
        """Ensure this endpoint is read-only."""
        url = self.get_url('goal-detail', args=[self.goal.id])
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_enroll_unathenticated(self):
        url = self.get_url('goal-enroll', args=[self.goal.id])
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_enroll(self):
        User = get_user_model()
        user = User.objects.create_user('x', 'a@b.xyz', 'asdf')
        url = self.get_url('goal-enroll', args=[self.goal.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + user.auth_token.key
        )
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['message'],
            "Your request has been scheduled and your goals "
            "should appear in your feed soon."
        )
        user.delete()

    def test_set_order(self):
        """Ensure the GoalViewSet.set_order detail_route updates the
        Goal's sequence_order"""
        url = reverse('goal-order', args=[self.goal.id])
        payload = {'sequence_order': 1}

        # check the pre-condition
        self.assertEqual(self.goal.sequence_order, 0)

        # But not for Anonymous requests...
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated requests...
        User = get_user_model()
        content_author_group = get_or_create_content_authors()
        args = ("author", "author@example.com", "pass")
        user = User.objects.create_user(*args)
        user.groups.add(content_author_group)

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + user.auth_token.key
        )
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Goal.objects.get(pk=self.goal.id).sequence_order, 1)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestTriggerAPI(V2APITestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(
            username="test",
            email="test@example.com",
        )
        self.default_trigger = Trigger.objects.create(name="Default")
        self.trigger = Trigger.objects.create(
            user=self.user,
            name='Test'
        )
        self.payload = {
            'name': 'Custom Trigger',
            'time': '14:30',
            'trigger_date': '2016-02-25',
            'recurrences': 'RRULE:FREQ=DAILY',
        }

    def tearDown(self):
        Trigger.objects.all().delete()

    def test_get_trigger_list(self):
        """Anon users see no triggers. Auth'd users should see their own"""
        url = self.get_url('trigger-list')

        # Anonymous requests...
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated requests...
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        obj = response.data['results'][0]
        self.assertEqual(obj['id'], self.trigger.id)
        self.assertEqual(obj['name'], self.trigger.name)
        self.assertEqual(obj['time'], self.trigger.time)
        self.assertEqual(obj['trigger_date'], self.trigger.trigger_date)
        self.assertEqual(obj['recurrences'], self.trigger.recurrences)
        self.assertEqual(
            obj['recurrences_display'],
            self.trigger.recurrences_as_text()
        )
        self.assertEqual(obj['next'], self.trigger.next())

    def test_post_trigger_list_unauthd(self):
        """un-Auth'd users should not be able to create a new trigger."""
        url = self.get_url('trigger-list')
        response = self.client.post(url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_trigger_list_authd(self):
        """POST should be allowed for authenticated users"""
        url = self.get_url('trigger-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_trigger_detail_unauthd(self):
        url = self.get_url('trigger-detail', args=[self.trigger.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_trigger_detail_authd(self):
        url = self.get_url('trigger-detail', args=[self.trigger.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_trigger_detail_unauthd(self):
        url = self.get_url('trigger-detail', args=[self.trigger.id])
        response = self.client.put(url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_trigger_list_authd(self):
        """PUT should be allowed for authenticated users"""
        url = self.get_url('trigger-detail', args=[self.trigger.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, {'disabled': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Trigger.objects.get(pk=self.trigger.id).disabled)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestBehaviorAPI(V2APITestCase):

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
        url = self.get_url('behavior-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        obj = response.data['results'][0]
        self.assertEqual(obj['id'], self.behavior.id)
        self.assertEqual(obj['title'], self.behavior.title)
        self.assertEqual(obj['description'], self.behavior.description)
        self.assertEqual(obj['html_description'], self.behavior.rendered_description)
        self.assertEqual(obj['more_info'], self.behavior.more_info)
        self.assertEqual(obj['html_more_info'], self.behavior.rendered_more_info)
        self.assertEqual(len(obj['goals']), 1)  # Should have 1 goal
        self.assertEqual(obj['goals'][0], self.goal.id)
        self.assertEqual(obj['actions_count'], self.behavior.action_set.count())

    def test_behavior_list_by_category_id(self):
        """Ensure we can filter by category.id."""
        # Create another Behavior (with no Category)
        b = Behavior.objects.create(title="ignore me")
        b.publish()
        b.save()

        url = self.get_url('behavior-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}&category={1}".format(url, self.category.id)
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

        url = self.get_url('behavior-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}&category={1}".format(url, self.category.title_slug)
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

        url = self.get_url('behavior-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}&goal={1}".format(url, self.goal.id)
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

        url = self.get_url('behavior-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}&goal={1}".format(url, self.goal.title_slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.behavior.id)

        # Clean up.
        b.delete()

    def test_post_behavior_list(self):
        """Ensure this endpoint is read-only."""
        url = self.get_url('behavior-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_behavior_detail(self):
        url = self.get_url('behavior-detail', args=[self.behavior.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.behavior.id)

    def test_post_behavior_detail(self):
        """Ensure this endpoint is read-only."""
        url = self.get_url('behavior-detail', args=[self.behavior.id])
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_set_order(self):
        """Ensure the BehaviorViewSet.set_order detail_route updates the
        Behavior's sequence_order"""
        url = reverse('behavior-order', args=[self.behavior.id])
        payload = {'sequence_order': 1}

        # check the pre-condition
        self.assertEqual(self.behavior.sequence_order, 0)

        # But not for Anonymous requests...
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated requests...
        User = get_user_model()
        content_author_group = get_or_create_content_authors()
        args = ("author", "author@example.com", "pass")
        user = User.objects.create_user(*args)
        user.groups.add(content_author_group)

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + user.auth_token.key
        )
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Behavior.objects.get(pk=self.behavior.id).sequence_order, 1)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestActionAPI(V2APITestCase):

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
        url = self.get_url('action-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        obj = response.data['results'][0]
        self.assertEqual(obj['id'], self.action.id)
        self.assertEqual(obj['title'], self.action.title)
        self.assertEqual(obj['description'], self.action.description)
        self.assertEqual(obj['html_description'], self.action.rendered_description)
        self.assertEqual(obj['more_info'], self.action.more_info)
        self.assertEqual(obj['html_more_info'], self.action.rendered_more_info)
        self.assertEqual(obj['behavior'], self.behavior.id)

    def test_action_list_by_category_id(self):
        """Ensure we can filter by category.id."""
        # Create another Action (with no Category)
        b = Behavior.objects.create(title='ignore me')
        b.publish()
        b.save()

        a = Action.objects.create(title="ignore me", behavior=b)
        a.publish()
        a.save()

        url = self.get_url('action-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}&category={1}".format(url, self.category.id)
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

        url = self.get_url('action-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}&category={1}".format(url, self.category.title_slug)
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

        url = self.get_url('action-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}&goal={1}".format(url, self.goal.id)
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

        url = self.get_url('action-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}&goal={1}".format(url, self.goal.title_slug)
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

        url = self.get_url('action-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}&behavior={1}".format(url, self.behavior.id)
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

        url = self.get_url('action-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Check the filtered result
        url = "{0}&behavior={1}".format(url, self.behavior.title_slug)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.action.id)

        # Clean up.
        a.delete()
        b.delete()

    def test_post_action_list(self):
        """Ensure this endpoint is read-only."""
        url = self.get_url('action-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_action_detail(self):
        url = self.get_url('action-detail', args=[self.action.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.action.id)

    def test_post_action_detail(self):
        """Ensure this endpoint is read-only."""
        url = self.get_url('action-detail', args=[self.action.id])
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_set_order(self):
        """Ensure the ActionViewSet.set_order detail_route updates the
        Action's sequence_order"""
        url = reverse('action-order', args=[self.action.id])
        payload = {'sequence_order': 100}

        # check the pre-condition
        self.assertNotEqual(self.action.sequence_order, 100)

        # But not for Anonymous requests...
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated requests...
        User = get_user_model()
        content_author_group = get_or_create_content_authors()
        args = ("author", "author@example.com", "pass")
        user = User.objects.create_user(*args)
        user.groups.add(content_author_group)

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + user.auth_token.key
        )
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Action.objects.get(pk=self.action.id).sequence_order, 100)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestUserGoalAPI(V2APITestCase):

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
        url = self.get_url('usergoal-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usergoal_list_authenticated(self):
        """Ensure authenticated requests DO expose results."""
        url = self.get_url('usergoal-list')
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
        self.assertTrue(response.data['results'][0]['editable'])

    def test_post_usergoal_list_unathenticated(self):
        """Unauthenticated requests should not be allowed to post new UserGoals"""
        url = self.get_url('usergoal-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_usergoal_list_athenticated(self):
        """Authenticated users Should be able to create a UserGoal."""
        newgoal = Goal.objects.create(title="New", subtitle="New")

        url = self.get_url('usergoal-list')
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

        url = self.get_url('usergoal-list')
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
        url = self.get_url('usergoal-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        # Post an ID to which the user already has an association
        response = self.client.post(url, {'goal': self.ug.goal.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_usergoal_detail_unauthed(self):
        """Ensure unauthenticated users cannot view this endpoint."""
        url = self.get_url('usergoal-detail', args=[self.ug.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_usergoal_detail(self):
        """Ensure authenticated users can view this endpoint."""
        url = self.get_url('usergoal-detail', args=[self.ug.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_usergoal_detail_not_allowed(self):
        """Ensure POSTing to the detail endpoint is not allowed."""
        url = self.get_url('usergoal-detail', args=[self.ug.id])
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
        url = self.get_url('usergoal-detail', args=[self.ug.id])
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
        url = self.get_url('usergoal-detail', args=[self.ug.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_usergoal_detail(self):
        """Ensure authenticated users can delete."""
        url = self.get_url('usergoal-detail', args=[self.ug.id])
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

        url = self.get_url('usergoal-list')
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

        url = self.get_url('usergoal-list')
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
class TestUserBehaviorAPI(V2APITestCase):

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

        self.action1 = Action.objects.create(title="A1", behavior=self.behavior)
        self.action1.default_trigger = mommy.make(Trigger)
        self.action1.publish()
        self.action1.save()

        self.action2 = Action.objects.create(title="A2", behavior=self.behavior)
        self.action2.default_trigger = mommy.make(Trigger)
        self.action2.publish()
        self.action2.save()

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
        url = self.get_url('userbehavior-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_userbehavior_list_authenticated(self):
        """Ensure authenticated requests DO expose results."""
        url = self.get_url('userbehavior-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        self.assertTrue(response.data['results'][0]['editable'])
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
        url = self.get_url('userbehavior-list')
        url = "{0}&goal={1}".format(url, self.goal.id)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # Test with goal title_slug
        url = self.get_url('userbehavior-list')
        url = "{0}&goal={1}".format(url,  self.goal.title_slug)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_post_userbehavior_list_unathenticated(self):
        """Unauthenticated requests should not be allowed to post"""
        url = self.get_url('userbehavior-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_userbehavior_list_athenticated(self):
        """Authenticated users Should be able to create a UserBehavior."""
        newbehavior = Behavior.objects.create(title="New")

        url = self.get_url('userbehavior-list')
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

        url = self.get_url('userbehavior-list')
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
        url = self.get_url('userbehavior-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        # Post an ID to which the user already has an association
        response = self.client.post(url, {'behavior': self.ub.behavior.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_userbehavior_detail_unauthed(self):
        """Ensure unauthenticated users cannot view this endpoint."""
        url = self.get_url('userbehavior-detail', args=[self.ub.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_userbehavior_detail(self):
        """Ensure authenticated users can view this endpoint."""
        url = self.get_url('userbehavior-detail', args=[self.ub.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_userbehavior_detail_not_allowed(self):
        """Ensure POSTing to the detail endpoint is not allowed."""
        url = self.get_url('userbehavior-detail', args=[self.ub.id])
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
        url = self.get_url('userbehavior-detail', args=[self.ub.id])
        response = self.client.put(url, {'behavior': 1})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_userbehavior_detail_authenticated(self):
        """PUT requests should update a UserBehavior (sorta). While this is
        technically allowed, it doesn't really do much without providing
        a custom trigger information.

        Essentially, PUTing {user: <id>, behavior: <id>} should update, but
        wouldn't change any information.

        """
        url = self.get_url('userbehavior-detail', args=[self.ub.id])
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
        url = self.get_url('userbehavior-detail', args=[self.ub.id])
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
        url = self.get_url('userbehavior-detail', args=[self.ub.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_userbehavior_detail(self):
        """Ensure authenticated users can delete."""
        url = self.get_url('userbehavior-detail', args=[self.ub.id])
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

        url = self.get_url('userbehavior-list')
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

        url = self.get_url('userbehavior-list')
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

    def test_delete_userbehavior_should_delete_useractions(self):
        """Ensure authenticated users can delete their UserBehaviors, but that
        doing so also deletes the related UserAction objects."""

        # Ensure the user has selected the child actions
        UserAction.objects.get_or_create(user=self.user, action=self.action1)
        UserAction.objects.get_or_create(user=self.user, action=self.action2)
        self.assertEqual(self.user.useraction_set.count(), 2)

        url = self.get_url('userbehavior-detail', args=[self.ub.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify side-effects
        userbehaviors = self.user.userbehavior_set.filter(id=self.ub.id)
        self.assertEqual(userbehaviors.count(), 0)
        useractions = self.user.useraction_set.filter(
            action__behavior=self.behavior)
        self.assertEqual(useractions.count(), 0)

    def test_post_userbehavior_with_parent_data(self):
        """POSTing to create a UserBehavior with parent object IDs"""
        category = mommy.make(Category, title="cat", state="published")
        goal = mommy.make(Goal, title="goal", state="published")
        goal.categories.add(self.category)
        behavior = mommy.make(Behavior, title="behavior", state="published")
        behavior.goals.add(goal)

        url = self.get_url('userbehavior-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )

        post_data = {
            'category': category.id,
            'goal': goal.id,
            'behavior': behavior.id,
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('behavior', response.data)
        self.assertEqual(response.data['behavior']['title'], 'behavior')

        # Clean up.
        behavior.delete()
        goal.delete()
        category.delete()

    def test_disable(self):
        """Test disabling all Actions/Triggers within a behavior."""
        url = reverse('userbehavior-disable', args=[self.ub.id])
        payload = {'disabled': '1'}

        # Create some UserActions and assign them to the user
        ua1 = UserAction.objects.create(user=self.user, action=self.action1)
        ua2 = UserAction.objects.create(user=self.user, action=self.action2)
        self.user.useraction_set.add(ua1)
        self.user.useraction_set.add(ua2)

        # Now let's do the Request.
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for ua in self.user.useraction_set.filter(pk__in=[ua1.pk, ua2.pk]):
            self.assertTrue(ua.custom_trigger.disabled)

        # Clean up
        ua1.delete()
        ua2.delete()


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestUserActionAPI(V2APITestCase):

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
        url = self.get_url('useraction-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_useraction_list_authenticated(self):
        """Ensure authenticated requests DO expose results."""
        url = self.get_url('useraction-list')
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
        self.assertIn('action', ua)
        self.assertIn('trigger', ua)
        self.assertIn('created_on', ua)
        self.assertEqual(ua['user'], self.user.id)
        self.assertEqual(ua['action']['id'], self.action.id)
        self.assertEqual(ua['action']['title'], self.action.title)
        self.assertTrue(ua['editable'])

    def test_get_useraction_list_with_filters(self):
        # Test with goal id
        url = self.get_url('useraction-list')
        url = "{0}&goal={1}".format(url, self.goal.id)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # Test with category title_slug filter
        url = self.get_url('useraction-list')
        url = "{0}&category={1}".format(url, self.category.title_slug)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # Test with category id filter
        url = self.get_url('useraction-list')
        url = "{0}&category={1}".format(url, self.category.id)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # Test with WRONG category id filter
        url = self.get_url('useraction-list')
        url = "{0}&category=99999".format(url)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

        # Test with goal title_slug
        url = self.get_url('useraction-list')
        url = "{0}&goal={1}".format(url, self.goal.title_slug)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # Test with Behavior id
        url = self.get_url('useraction-list')
        url = "{0}&behavior={1}".format(url, self.behavior.id)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # Test with Behavior title_slug
        url = self.get_url('useraction-list')
        url = "{0}&behavior={1}".format(url, self.behavior.title_slug)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_get_useraction_list_filtered_on_today(self):
        # Test with goal id
        url = self.get_url('useraction-list')
        url = "{0}&today=1".format(url)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_post_useraction_list_unathenticated(self):
        """Unauthenticated requests should not be allowed to post"""
        url = self.get_url('useraction-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_useraction_list_athenticated(self):
        """Authenticated users should be able to create a UserAction."""
        newaction = Action.objects.create(title="New", behavior=self.behavior)

        url = self.get_url('useraction-list')
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

        url = self.get_url('useraction-list')
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

        url = self.get_url('useraction-list')
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

        url = self.get_url('useraction-list')
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
        url = self.get_url('useraction-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        # Post an ID to which the user already has an association
        response = self.client.post(url, {'action': self.ua.action.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_useraction_detail_unauthenticated(self):
        """Ensure unauthenticated users cannot view this endpoint."""
        url = self.get_url('useraction-detail', args=[self.ua.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_useraction_detail_authenticated(self):
        """Ensure authenticated users can view this endpoint."""
        url = self.get_url('useraction-detail', args=[self.ua.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_useraction_detail_not_allowed(self):
        """Ensure POSTing to the detail endpoint is not allowed."""
        url = self.get_url('useraction-detail', args=[self.ua.id])
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
        url = self.get_url('useraction-detail', args=[self.ua.id])
        response = self.client.put(url, {'action': 1})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_useraction_detail_authenticated_with_no_data(self):
        """PUT requests should update a UserAction (sorta). While this is
        technically allowed, it doesn't really do much without providing
        a custom trigger information.

        Essentially, PUTing {user: <id>, action: <id>} should update, but
        wouldn't change any information.

        """
        url = self.get_url('useraction-detail', args=[self.ua.id])
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
        url = self.get_url('useraction-detail', args=[self.ua.id])
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
        url = self.get_url('useraction-detail', args=[self.ua.id])
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
        self.assertFalse(ua.custom_trigger.disabled)

    def test_put_useraction_detail_disable_custom_trigger(self):
        """PUT requests should be able to disable a custom trigger"""
        url = self.get_url('useraction-detail', args=[self.ua.id])
        payload = {
            'custom_trigger_disabled': True,
            'custom_trigger_date': '2222-12-25',
            'custom_trigger_time': '9:30',
            'custom_trigger_rrule': 'RRULE:FREQ=WEEKLY;BYDAY=MO',
        }
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test that the other trigger fields are unchanged.
        ua = UserAction.objects.get(pk=self.ua.id)
        self.assertIsNotNone(ua.custom_trigger)
        self.assertEqual(ua.get_custom_trigger_name(), ua.custom_trigger.name)
        self.assertEqual(
            ua.custom_trigger.recurrences_as_text(),
            "weekly, each Monday"
        )
        self.assertEqual(ua.custom_trigger.time, time(9, 30))
        self.assertEqual(ua.custom_trigger.trigger_date, date(2222, 12, 25))
        self.assertTrue(ua.custom_trigger.disabled)

    def test_put_useraction_custom_trigger_updates(self):
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

        url = self.get_url('useraction-detail', args=[self.ua.id])
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
        self.assertFalse(ua.custom_trigger.disabled)

        # clean up
        Trigger.objects.filter(id=custom_trigger.id).delete()

    def test_put_useraction_custom_trigger_disable(self):
        """PUT requests can disable custom triggers."""
        # Create a Custom trigger for our UserAction
        custom_trigger = Trigger.objects.create_for_user(
            user=self.ua.user,
            name="custom trigger for useraction-{0}".format(self.ua.id),
            time=time(11, 30),
            date=date(2000, 1, 2),
            rrule="RRULE:FREQ=DAILY",
            disabled=False
        )
        self.ua.custom_trigger = custom_trigger
        self.ua.save()

        # Ensure the trigger is enabled by default.
        self.assertFalse(self.ua.custom_trigger.disabled)

        url = self.get_url('useraction-detail', args=[self.ua.id])
        payload = {
            'custom_trigger_disabled': True
        }
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that the Trigger got updated.
        ua = UserAction.objects.get(pk=self.ua.id)
        self.assertTrue(ua.custom_trigger.disabled)

        # clean up
        Trigger.objects.filter(id=ua.custom_trigger.id).delete()

    def test_put_useraction_empty_custom_trigger_disable(self):
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

        url = self.get_url('useraction-detail', args=[self.ua.id])
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
        url = self.get_url('useraction-detail', args=[self.ua.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_useraction_detail_authenticated(self):
        """Ensure authenticated users can delete."""
        url = self.get_url('useraction-detail', args=[self.ua.id])
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

        url = self.get_url('useraction-list')
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

        url = self.get_url('useraction-list')
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
        url = self.get_url('useraction-complete', args=[self.ua.id])
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

    def test_post_useraction_with_parent_data(self):
        """POSTing to create a UserAction with parent object IDs"""
        category = mommy.make(Category, title="cat", state="published")
        goal = mommy.make(Goal, title="goal", state="published")
        goal.categories.add(self.category)
        behavior = mommy.make(Behavior, title="behavior", state="published")
        behavior.goals.add(goal)
        action = mommy.make(Action, title="a", behavior=behavior, state='published')

        url = self.get_url('useraction-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )

        post_data = {
            'category': category.id,
            'goal': goal.id,
            'behavior': behavior.id,
            'action': action.id,
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('action', response.data)
        self.assertEqual(response.data['action']['title'], 'a')

        # Clean up.
        action.delete()
        behavior.delete()
        goal.delete()
        category.delete()


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestUserCategoryAPI(V2APITestCase):

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
        # TODO: Figure out how to test icon/image fields and their inclusion
        # in the api. Maybe useful: http://goo.gl/nh7Vl4

        # Assign a Category to the User
        self.uc = UserCategory.objects.create(user=self.user, category=self.category)

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(id=self.user.id).delete()
        Category.objects.filter(id=self.category.id).delete()
        UserCategory.objects.filter(id=self.uc.id).delete()

    def test_get_usercategory_list_unauthenticated(self):
        """Ensure un-authenticated requests don't expose any results."""
        url = self.get_url('usercategory-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_usercategory_list_authenticated(self):
        """Ensure authenticated requests DO expose results."""
        url = self.get_url('usercategory-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # check the fields of a result object.
        self.assertIn("id", response.data['results'][0])
        self.assertIn("category", response.data['results'][0])
        self.assertIn("editable", response.data['results'][0])
        self.assertIn("order", response.data['results'][0]['category'])
        self.assertIn("title", response.data['results'][0]['category'])
        self.assertIn("description", response.data['results'][0]['category'])
        self.assertIn("icon_url", response.data['results'][0]['category'])
        self.assertIn("image_url", response.data['results'][0]['category'])
        self.assertIn("color", response.data['results'][0]['category'])
        self.assertIn("secondary_color", response.data['results'][0]['category'])
        self.assertIn("selected_by_default", response.data['results'][0]['category'])
        self.assertIn("object_type", response.data['results'][0]['category'])

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
        self.assertTrue(response.data['results'][0]['editable'])
        # TODO: it'd be nice if these fields actually had data.
        self.assertEqual(response.data['results'][0]['category']['image_url'], None)
        self.assertEqual(response.data['results'][0]['category']['icon_url'], None)

    def test_post_usercategory_list_unauthenticated(self):
        """POST should not be allowed for unauthenticated users"""
        url = self.get_url('usercategory-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_usercategory_list_authenticated(self):
        """POST should be allowed for authenticated users"""
        newcat = Category.objects.create(order=2, title="NEW")

        url = self.get_url('usercategory-list')
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

        url = self.get_url('usercategory-list')
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
        url = self.get_url('usercategory-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        # Post an ID to which the user already has an association
        response = self.client.post(url, {'category': self.uc.category.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_usercategory_detail_unauthenticated(self):
        """Ensure unauthenticated users cannot view this endpoint."""
        url = self.get_url('usercategory-detail', args=[self.uc.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_usercategory_detail_authenticated(self):
        """Ensure authenticated users can view this endpoint."""
        url = self.get_url('usercategory-detail', args=[self.uc.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_usercategory_detail_not_allowed(self):
        """Ensure POSTing to the detail endpoint is not allowed."""
        url = self.get_url('usercategory-detail', args=[self.uc.id])
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
        url = self.get_url('usercategory-detail', args=[self.uc.id])
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
        url = self.get_url('usercategory-detail', args=[self.uc.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_usercategory_detail_authenticated(self):
        """Ensure authenticated users can delete."""
        url = self.get_url('usercategory-detail', args=[self.uc.id])
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

        url = self.get_url('usercategory-list')
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

        url = self.get_url('usercategory-list')
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
class TestPackageEnrollmentAPI(V2APITestCase):

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

        self.url = self.get_url('packageenrollment-list')
        self.detail_url = self.get_url(
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
        url = self.get_url('packageenrollment-detail', args=[package.id])
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
        url = self.get_url('packageenrollment-accept', args=[package.id])
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
class TestCustomGoalAPI(V2APITestCase):

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
        url = self.get_url('customgoal-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customgoal_list_authenticated(self):
        """Ensure authenticated requests DO expose results."""
        url = self.get_url('customgoal-list')
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
        url = self.get_url('customgoal-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_customgoal_list_athenticated(self):
        """Authenticated users should be able to create a CustomGoal."""
        url = self.get_url('customgoal-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, {"title": "New Custom Goal"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomGoal.objects.filter(user=self.user).count(), 2)

    def test_get_customgoal_detail_unauthed(self):
        """Ensure unauthenticated users cannot view this endpoint."""
        url = self.get_url('customgoal-detail', args=[self.customgoal.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_customgoal_detail(self):
        """Ensure authenticated users can view this endpoint."""
        url = self.get_url('customgoal-detail', args=[self.customgoal.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_customgoal_detail_not_allowed(self):
        """Ensure POSTing to the detail endpoint is not allowed."""
        url = self.get_url('customgoal-detail', args=[self.customgoal.id])
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
        url = self.get_url('customgoal-detail', args=[self.customgoal.id])
        response = self.client.put(url, {'title': 'Altered'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_customgoal_detail(self):
        """Ensure PUTing to the detail endpoint updates."""
        url = self.get_url('customgoal-detail', args=[self.customgoal.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.put(url, {'title': 'Altered'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cg = CustomGoal.objects.get(pk=self.customgoal.id)
        self.assertEqual(cg.title, 'Altered')

    def test_delete_customgoal_detail_unauthed(self):
        """Ensure unauthenticated users cannot delete."""
        url = self.get_url('customgoal-detail', args=[self.customgoal.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_customgoal_detail(self):
        """Ensure authenticated users can delete."""
        cg = CustomGoal.objects.create(user=self.user, title="DELETE")
        ca1 = mommy.make(CustomAction, customgoal=cg)
        ca2 = mommy.make(CustomAction, customgoal=cg)

        url = self.get_url('customgoal-detail', args=[cg.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CustomGoal.objects.filter(title='DELETE').exists())

        # Child actions should have also been deleted
        self.assertFalse(CustomAction.objects.filter(id=ca1.id).exists())
        self.assertFalse(CustomAction.objects.filter(id=ca2.id).exists())


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestCustomActionAPI(V2APITestCase):

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
        url = self.get_url('customaction-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customaction_list_authenticated(self):
        """Ensure authenticated requests DO expose results."""
        url = self.get_url('customaction-list')
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

    def test_customaction_list_filtered(self):
        """Ensure results can be filtered by custom goal id or title slug."""
        url = self.get_url('customaction-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )

        # Filter by parent goal ID.
        filtered_url = url + "&customgoal={}".format(self.customgoal.id)
        response = self.client.get(filtered_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # Filter by parent goal title slug.
        filtered_url = url + "&customgoal={}".format(self.customgoal.title_slug)
        response = self.client.get(filtered_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # Filter by Non-existing parent goal ID (should return 0 results)
        filtered_url = url + "&customgoal=9999999"
        response = self.client.get(filtered_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_post_customaction_list_unathenticated(self):
        """Unauthenticated requests should not be allowed to post new
        CustomActions"""
        url = self.get_url('customaction-list')
        response = self.client.post(url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_customaction_list_athenticated(self):
        """Authenticated users should be able to create a CustomAction."""
        url = self.get_url('customaction-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomAction.objects.filter(user=self.user).count(), 2)

    def test_get_customaction_detail_unauthed(self):
        """Ensure unauthenticated users cannot view this endpoint."""
        url = self.get_url('customaction-detail', args=[self.customaction.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_customaction_detail(self):
        """Ensure authenticated users can view this endpoint."""
        url = self.get_url('customaction-detail', args=[self.customaction.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_customaction_detail_not_allowed(self):
        """Ensure POSTing to the detail endpoint is not allowed."""
        url = self.get_url('customaction-detail', args=[self.customaction.id])
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
        url = self.get_url('customaction-detail', args=[self.customaction.id])
        response = self.client.put(url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_customaction_detail(self):
        """Ensure PUTing to the detail endpoint updates."""
        url = self.get_url('customaction-detail', args=[self.customaction.id])
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
        url = self.get_url('customaction-detail', args=[self.customaction.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_customaction_detail(self):
        """Ensure authenticated users can delete."""
        ca = CustomAction.objects.create(
            user=self.user,
            title="DELETE",
            customgoal=self.customgoal
        )
        url = self.get_url('customaction-detail', args=[ca.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CustomAction.objects.filter(title='DELETE').exists())

    def test_get_complete_unathenticated(self):
        url = self.get_url('customaction-complete', args=[self.customaction.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_complete_unathenticated(self):
        url = self.get_url('customaction-complete', args=[self.customaction.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_complete(self):
        """POSTing to the complete url should crate an UserCompletedCustomAction
        object for a user."""
        # We shouldn't have any just yet.
        qs = UserCompletedCustomAction.objects.filter(user=self.user)
        self.assertFalse(qs.exists())

        url = self.get_url('customaction-complete', args=[self.customaction.id])
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

        url = self.get_url('customaction-feedback', args=[self.customaction.id])
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
        url = self.get_url('customaction-feedback', args=[self.customaction.id])
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
        url = self.get_url('customaction-detail', args=[self.customaction.id])
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
        url = self.get_url('customaction-detail', args=[self.customaction.id])
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

    def test_put_detail_authenticated_with_only_custom_trigger(self):
        """PUT requests containting ONLY custom trigger details, should create
        a custom trigger (if that field was previously null) for the
        CustomAction.

        """
        url = self.get_url('customaction-detail', args=[self.customaction.id])
        payload = {
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

        url = self.get_url('customaction-detail', args=[self.customaction.id])
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

    def test_put_custom_trigger_udpates_with_only_trigger_data(self):
        """When we have an existing custom trigger, putting new values should
        update it (this time ONLY including the trigger data)."""

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

        url = self.get_url('customaction-detail', args=[self.customaction.id])
        payload = {
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

        url = self.get_url('customaction-detail', args=[self.customaction.id])
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


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
@override_settings(CACHES=TEST_CACHES)
class TestDailyProgressAPI(V2APITestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user('dp', 'dp@example.com', 'dp-asdf')
        self.dp = DailyProgress.objects.create(user=self.user)
        self.payload = {'actions_completed': 1}

    def tearDown(self):
        DailyProgress.objects.filter(id=self.dp.id).delete()

    def test_get_dailyprogress_list_anon(self):
        url = self.get_url('dailyprogress-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_dailyprogress_list(self):
        url = self.get_url('dailyprogress-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_post_dailyprogress_list_unauthed(self):
        """Ensure this endpoint is read-only."""
        url = self.get_url('dailyprogress-list')
        response = self.client.post(url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_dailyprogress_list(self):
        """Ensure this endpoint is read-only."""
        url = self.get_url('dailyprogress-list')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It shouldn't get created, it should just update the existing object
        self.assertEqual(response.data['id'], self.dp.id)
        self.assertEqual(response.data['actions_completed'], 1)

    def test_get_dailyprogress_detail_anon(self):
        url = self.get_url('dailyprogress-detail', args=[self.dp.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_dailyprogress_detail(self):
        url = self.get_url('dailyprogress-detail', args=[self.dp.id])
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.dp.id)

    def test_post_dailyprogress_detail(self):
        url = self.get_url('dailyprogress-detail', args=[self.dp.id])
        # Not allowed for anon...
        response = self.client.post(url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # nor for authenticated users
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        response = self.client.post(url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_post_dailyprogress_checkin_anon(self):
        url = self.get_url('dailyprogress-checkin')
        response = self.client.post(url, {'goal': 1, 'daily_checkin': 1})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_dailyprogress_checkin(self):
        url = self.get_url('dailyprogress-checkin')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        # The user must have adopted this goal for this to work
        goal = Goal.objects.create(title="Checkin", subtitle="...")
        goal.publish()
        goal.save()
        UserGoal.objects.create(goal=goal, user=self.user)

        payload = {'goal': goal.id, 'daily_checkin': 4}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected = {'goal-{}'.format(goal.id): 4}
        self.assertEqual(response.data['goal_status'], expected)

    def test_get_dailyprogress_behavior_status_unauthed(self):
        url = self.get_url('dailyprogress-behaviors')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_dailyprogress_behavior_status_unauthed(self):
        url = self.get_url('dailyprogress-behaviors')
        response = self.client.post(url, {'behavior': 1, 'bucket': 'core'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_dailyprogress_behavior_status(self):
        url = self.get_url('dailyprogress-behaviors')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        # When the user has not behaviors nor any progress data
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {})

        # When the user DOES have behaviors and progress data
        behavior = Behavior.objects.create(title='B')
        ub = UserBehavior.objects.create(behavior=behavior, user=self.user)
        self.dp.set_status(behavior, 'core')
        self.dp.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = {'behavior-{}'.format(behavior.id): 'core'}
        self.assertEqual(response.data, expected)

        # clean up
        behavior.delete()
        ub.delete()
        self.dp.behaviors_status = {}
        self.dp.save()

    def test_post_dailyprogress_behavior_status_invalid_data(self):
        url = self.get_url('dailyprogress-behaviors')
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.user.auth_token.key
        )
        payload = {
            'behavior': '9999999999',
            'bucket': 'not-a-valid-bucket',
        }
        # POST: invalid bucket name
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Invalid bucket name'})

        # POST: behavior not owned by the user
        payload['bucket'] = 'core'
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected = {'error': "UserBehavior matching query does not exist."}
        self.assertEqual(response.data, expected)

    def test_streaks(self):
        """
        /api/users/progress/streaks.<format>/
            goals.api.DailyProgressViewSet
            dailyprogress-streaks

        /api/users/progress/streaks/
            goals.api.DailyProgressViewSet
            dailyprogress-streaks

        """
        User = get_user_model()
        user = User.objects.create_user('x', 'x@x.x', 'xxx')
        today = timezone.now()

        # Generate some data for the past 2 days.
        # with patch('goals.models.progress.timezone.now') as mock_now:
        with patch('django.db.models.fields.timezone.now') as mock_now:
            # 2days ago, 8am UTC
            dt = today - timedelta(days=2)
            mock_now.return_value = tzdt(dt.year, dt.month, dt.day, 8, 0)
            DailyProgress.objects.create(
                user=user,
                actions_total=1,
                actions_completed=1,
                behaviors_total=1,
                checkin_streak=1,
            )

            # 1 day ago, 8am UTC
            dt = today - timedelta(days=1)
            mock_now.return_value = tzdt(dt.year, dt.month, dt.day, 8, 0)
            DailyProgress.objects.create(
                user=user,
                actions_total=1,
                actions_completed=1,
                behaviors_total=1,
                checkin_streak=1,
            )

        # GET request should return some data
        url = self.get_url('dailyprogress-streaks')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.auth_token.key)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(sum(d['count'] for d in response.data.get('results')), 2)

        with patch('goals.user_feed.timezone.now') as mock_now:
            mock_now.return_value = tzdt(today.year, today.month, today.day, 20, 1)
            url = self.get_url('dailyprogress-streaks')
            self.client.credentials(HTTP_AUTHORIZATION='Token ' + user.auth_token.key)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(sum(d['count'] for d in response.data.get('results')), 2)
