from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .. models import (
    Action,
    Behavior,
    Category,
    Goal,
    Trigger,
)


class TestCategoryAPI(APITestCase):

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
            notes="Some notes"
        )

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
        self.assertEqual(c['title'], self.category.title)
        self.assertEqual(c['title_slug'], self.category.title_slug)

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


class TestGoalAPI(APITestCase):

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
            notes="Some notes"
        )
        self.goal = Goal.objects.create(
            title="Test Goal",
            subtitle="A subtitle",
            description="A Description",
            outcome="The outcome"
        )
        self.goal.categories.add(self.category)

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
        self.assertEqual(obj['subtitle'], self.goal.subtitle)
        self.assertEqual(obj['description'], self.goal.description)

    def test_goal_list_by_category(self):
        """Ensure we can filter by category."""
        # Create another Goal (not in a catgory)
        g = Goal.objects.create(title="ignore me")

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


class TestTriggerAPI(APITestCase):

    def setUp(self):
        self.trigger = Trigger.objects.create(name="Test Trigger")

    def tearDown(self):
        Trigger.objects.filter(id=self.trigger.id).delete()

    def test_trigger_list(self):
        url = reverse('trigger-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        obj = response.data['results'][0]
        self.assertEqual(obj['id'], self.trigger.id)
        self.assertEqual(obj['name'], self.trigger.name)

    def test_post_trigger_list(self):
        """Ensure this endpoint is read-only."""
        url = reverse('trigger-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_trigger_detail(self):
        url = reverse('trigger-detail', args=[self.trigger.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.trigger.id)

    def test_post_trigger_detail(self):
        """Ensure this endpoint is read-only."""
        url = reverse('trigger-detail', args=[self.trigger.id])
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class TestBehaviorAPI(APITestCase):

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
            notes="Some notes"
        )
        self.goal = Goal.objects.create(
            title="Test Goal",
            subtitle="A subtitle",
            description="A Description",
            outcome="The outcome"
        )
        self.behavior = Behavior.objects.create(
            title="Test Behavior",
            description="This is a test",
            informal_list="Do this",
        )
        self.behavior.categories.add(self.category)
        self.behavior.goals.add(self.goal)

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
        self.assertEqual(len(obj['goals']), 1)  # Should have 1 goal
        self.assertEqual(obj['goals'][0]['title'], self.goal.title)

    def test_behavior_list_by_category_id(self):
        """Ensure we can filter by category.id."""
        # Create another Behavior (with no Category)
        b = Behavior.objects.create(title="ignore me")

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


class TestActionAPI(APITestCase):

    def setUp(self):
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
            notes="Some notes"
        )
        self.goal = Goal.objects.create(
            title="Test Goal",
            subtitle="A subtitle",
            description="A Description",
            outcome="The outcome"
        )
        self.behavior = Behavior.objects.create(
            title="Test Behavior",
            description="This is a test",
            informal_list="Do this",
        )
        self.behavior.categories.add(self.category)
        self.behavior.goals.add(self.goal)

        self.action = Action.objects.create(
            title="Test Action",
            sequence_order=1,
            behavior=self.behavior,
            description="This is a test",
        )

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
        self.assertEqual(obj['behavior']['id'], self.behavior.id)

    def test_action_list_by_category_id(self):
        """Ensure we can filter by category.id."""
        # Create another Action (with no Category)
        b = Behavior.objects.create(title='ignore me')
        a = Action.objects.create(title="ignore me", behavior=b)

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
        a = Action.objects.create(title="ignore me", behavior=b)

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
        a = Action.objects.create(title="ignore me", behavior=b)

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
        a = Action.objects.create(title="ignore me", behavior=b)

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
        a = Action.objects.create(title="ignore me", behavior=b)

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
        a = Action.objects.create(title="ignore me", behavior=b)

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
