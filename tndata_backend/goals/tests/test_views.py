import pytz
from datetime import time

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import Client, TestCase

from .. models import (
    Category,
    Goal,
    Trigger,
    Behavior,
    Action,
)
from .. permissions import (
    get_or_create_content_admins,
    get_or_create_content_editors,
    get_or_create_content_authors,
    get_or_create_content_viewers,
)
from .. settings import DEFAULT_BEHAVIOR_TRIGGER_NAME


User = get_user_model()


class TestCaseWithGroups(TestCase):
    """A TestCase Subclass that adds additional data and/or features for test
    subclasses:

    * A `ua_client` attribute; an unauthenticated client.
    * Creates admin, author, editor, viewer users in the appropriate groups.

    """

    @classmethod
    def setUpTestData(cls):
        """Set up data for the whole Test Case; this method creates
        four classes of users by default (admin, editor, author, viewer).

        If you override this in a TestCase, be sure to call the superclass.

        """
        content_editor_group = get_or_create_content_editors()
        content_author_group = get_or_create_content_authors()
        content_viewer_group = get_or_create_content_viewers()
        content_admin_group = get_or_create_content_admins()

        args = ("admin", "admin@example.com", "pass")
        cls.admin = User.objects.create_superuser(*args)
        cls.admin.groups.add(content_admin_group)

        args = ("author", "author@example.com", "pass")
        cls.author = User.objects.create_user(*args)
        cls.author.groups.add(content_author_group)

        args = ("editor", "editor@example.com", "pass")
        cls.editor = User.objects.create_user(*args)
        cls.editor.groups.add(content_editor_group)

        args = ("viewer", "viewer@example.com", "pass")
        cls.viewer = User.objects.create_user(*args)
        cls.viewer.groups.add(content_viewer_group)


class TestIndexView(TestCaseWithGroups):
    # NOTE: tests are named with this convention:
    # test_[auth-group]_[http-verb]

    @classmethod
    def setUpClass(cls):
        super(cls, TestIndexView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client
        cls.url = reverse("goals:index")

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.client.logout()

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.client.logout()

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.client.logout()

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.client.logout()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)


class TestCategoryListView(TestCaseWithGroups):
    # NOTE: tests are named with this convention:
    # test_[auth-group]_[http-verb]

    @classmethod
    def setUpClass(cls):
        super(cls, TestCategoryListView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client
        cls.url = reverse("goals:category-list")

    @classmethod
    def setUpTestData(cls):
        super(cls, TestCategoryListView).setUpTestData()
        # Create a Category
        cls.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_list.html")
        self.assertIn("categories", resp.context)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_list.html")
        self.assertIn("categories", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_list.html")
        self.assertIn("categories", resp.context)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_list.html")
        self.assertIn("categories", resp.context)

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)


class TestCategoryDetailView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestCategoryDetailView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestCategoryDetailView).setUpTestData()
        # Create a Category
        cls.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )
        cls.url = cls.category.get_absolute_url()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_detail.html")
        self.assertContains(resp, self.category.title)
        self.assertIn("category", resp.context)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_detail.html")
        self.assertContains(resp, self.category.title)
        self.assertIn("category", resp.context)

    def test_editor_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_detail.html")
        self.assertContains(resp, self.category.title)
        self.assertIn("category", resp.context)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_detail.html")
        self.assertContains(resp, self.category.title)
        self.assertIn("category", resp.context)


class TestCategoryCreateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestCategoryCreateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client
        cls.url = reverse("goals:category-create")

    @classmethod
    def setUpTestData(cls):
        super(cls, TestCategoryCreateView).setUpTestData()
        # Create a Category
        cls.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_form.html")
        self.assertContains(resp, self.category.title)
        self.assertIn("categories", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_form.html")
        self.assertContains(resp, self.category.title)
        self.assertIn("categories", resp.context)

    def test_author_get(self):
        """Ensure Authors cannot create Categories."""
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_get(self):
        """Ensure Authors cannot create Categories."""
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_anon_post(self):
        payload = {'order': 2, 'title': 'New', 'description': 'Desc', 'color': '#f00'}
        resp = self.ua_client.post(self.url, payload)
        self.assertEqual(resp.status_code, 403)

    def test_admin_post(self):
        """Ensure Admins can create new Categories"""
        self.client.login(username="admin", password="pass")
        payload = {'order': 2, 'title': 'New', 'description': 'Desc', 'color': '#f00'}
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Category.objects.filter(title="New").exists())
        Category.objects.filter(title="New Category").delete()  # clean up

    def test_editor_post(self):
        """Ensure Editors can create new Categories"""
        self.client.login(username="editor", password="pass")
        payload = {'order': 2, 'title': 'New', 'description': 'Desc', 'color': '#f00'}
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Category.objects.filter(title="New").exists())
        Category.objects.filter(title="New").delete()  # clean up

    def test_author_post(self):
        """Ensure Authors cannot create new categories."""
        self.client.login(username="author", password="pass")
        payload = {'order': 2, 'title': 'New', 'description': 'Desc', 'color': '#f00'}
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_post(self):
        """Ensure Viewers cannot create new categories."""
        self.client.login(username="viewer", password="pass")
        payload = {'order': 2, 'title': 'New', 'description': 'Desc', 'color': '#f00'}
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 403)


class TestCategoryDuplicateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestCategoryDuplicateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestCategoryDuplicateView).setUpTestData()
        # Create a Category
        cls.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )
        cls.url = cls.category.get_duplicate_url()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_form.html")
        title_copy = "Copy of {0}".format(self.category.title)
        self.assertContains(resp, title_copy)
        self.assertIn("categories", resp.context)


class TestCategoryPublishView(TestCaseWithGroups):
    # NOTE: tests are named with this convention:
    # test_[auth-group]_[http-verb]

    @classmethod
    def setUpClass(cls):
        super(cls, TestCategoryPublishView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestCategoryPublishView).setUpTestData()
        # Create a Category
        cls.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )
        cls.url = cls.category.get_publish_url()

    def setUp(self):
        self.category.review()  # Must be pending review.
        self.category.save()

    def tearDown(self):
        self.category.draft()  # Revert to draft
        self.category.save()

    def test_anon_publish(self):
        self.ua_client.login(username="author", password="pass")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_admin_publish(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 302)
        state = Category.objects.get(pk=self.category.pk).state
        self.assertEqual(state, "published")

    def test_editor_publish(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 302)
        state = Category.objects.get(pk=self.category.pk).state
        self.assertEqual(state, "published")

    def test_author_publish(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_viewer_publish(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_anon_decline(self):
        resp = self.ua_client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_admin_decline(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 302)
        state = Category.objects.get(pk=self.category.pk).state
        self.assertEqual(state, "declined")

    def test_editor_decline(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 302)
        state = Category.objects.get(pk=self.category.pk).state
        self.assertEqual(state, "declined")

    def test_author_decline(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_viewer_decline(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 403)


class TestCategoryUpdateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestCategoryUpdateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestCategoryUpdateView).setUpTestData()
        # Create a Category
        cls.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )
        cls.url = cls.category.get_update_url()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        resp = self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_form.html")
        self.assertContains(resp, self.category.title)
        self.assertIn("categories", resp.context)

    def test_editor_get(self):
        resp = self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        resp = self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_get(self):
        resp = self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)


class TestCategoryDeleteView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestCategoryDeleteView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestCategoryDeleteView).setUpTestData()
        # Create a Category
        cls.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )
        cls.url = cls.category.get_delete_url()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        resp = self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_confirm_delete.html")
        self.assertIn("category", resp.context)

    def test_editor_get(self):
        resp = self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        resp = self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_get(self):
        resp = self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_anon_post(self):
        resp = self.ua_client.post(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_post(self):
        resp = self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("goals:index"))

    def test_editor_post(self):
        resp = self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("goals:index"))

    def test_author_post(self):
        resp = self.client.login(username="author", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_post(self):
        resp = self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)


class TestGoalListView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestGoalListView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client
        cls.url = reverse("goals:goal-list")

    @classmethod
    def setUpTestData(cls):
        super(cls, TestGoalListView).setUpTestData()
        # Create Goal
        cls.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
            outcome="An Outcome"
        )

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/goal_list.html")
        self.assertIn("goals", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)


class TestGoalDetailView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestGoalDetailView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestGoalDetailView).setUpTestData()
        # Create Goal
        cls.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
            outcome="An Outcome"
        )
        cls.url = cls.goal.get_absolute_url()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/goal_detail.html")
        self.assertContains(resp, self.goal.title)
        self.assertIn("goal", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)


class TestGoalCreateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestGoalCreateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client
        cls.url = reverse("goals:goal-create")

    @classmethod
    def setUpTestData(cls):
        super(cls, TestGoalCreateView).setUpTestData()
        # Create Goal
        cls.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
            outcome="An Outcome"
        )

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/goal_form.html")
        self.assertContains(resp, self.goal.title)
        self.assertIn("goals", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)


class TestGoalDuplicateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestGoalDuplicateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestGoalDuplicateView).setUpTestData()
        cls.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
            outcome="An Outcome"
        )
        cls.url = cls.goal.get_duplicate_url()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/goal_form.html")
        title_copy = "Copy of {0}".format(self.goal.title)
        self.assertContains(resp, title_copy)
        self.assertIn("goals", resp.context)


class TestGoalPublishView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestGoalPublishView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestGoalPublishView).setUpTestData()
        # Create Goal
        cls.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
            outcome="An Outcome"
        )
        cls.url = cls.goal.get_publish_url()

    def setUp(self):
        super(TestGoalPublishView, self).setUp()
        self.goal.review()
        self.goal.save()

    def tearDown(self):
        self.goal.draft()
        self.goal.save()

    def test_anon_publish(self):
        resp = self.ua_client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_admin_publish(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 302)
        state = Goal.objects.get(pk=self.goal.pk).state
        self.assertEqual(state, 'published')

    def test_editor_publish(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 302)
        state = Goal.objects.get(pk=self.goal.pk).state
        self.assertEqual(state, 'published')

    def test_author_publish(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_viewer_publish(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_anon_decline(self):
        resp = self.ua_client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_admin_decline(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 302)
        state = Goal.objects.get(pk=self.goal.pk).state
        self.assertEqual(state, "declined")

    def test_editor_decline(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 302)
        state = Goal.objects.get(pk=self.goal.pk).state
        self.assertEqual(state, "declined")

    def test_author_decline(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_viewer_decline(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 403)


class TestGoalUpdateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestGoalUpdateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestGoalUpdateView).setUpTestData()
        # Create a Category
        cls.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )
        cls.payload = {
            'categories': cls.category.id,
            'order': 1,
            'title': 'A',
            'description': 'B',
            'notes': '',
        }

    def setUp(self):
        # Re-create the goal
        self.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
            outcome="An Outcome",
            created_by=self.author
        )
        self.url = self.goal.get_update_url()

    def tearDown(self):
        Goal.objects.filter(id=self.goal.id).delete()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/goal_form.html")
        self.assertContains(resp, self.goal.title)
        self.assertIn("goals", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        """Ensure authors can update their own content."""
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get_other_object(self):
        """Ensure authors cannot update someone else's content."""
        g = Goal.objects.create(title="Other", created_by=self.editor)
        self.client.login(username="author", password="pass")
        resp = self.client.get(g.get_update_url())
        self.assertEqual(resp.status_code, 403)
        g.delete()  # Clean up

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_anon_post(self):
        resp = self.ua_client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)

    def test_admin_post(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Goal.objects.get(pk=self.goal.id).title, 'A')

    def test_editor_post(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Goal.objects.get(pk=self.goal.id).title, 'A')

    def test_editor_post_duplicate_title(self):
        """If you change the title of an existing object to somethign that
        would be a duplicate, the form should warn you (200 response) instead
        of throwing a 500 IntegrityError."""

        existing_title = "Title for Test Goal"  # A pre-existing title.
        goal = Goal.objects.create(
            title="Some Goal to Edit",
            created_by=self.editor
        )
        goal.categories.add(self.category)
        goal.save()

        self.client.login(username="editor", password="pass")
        resp = self.client.post(goal.get_update_url(), {
            'title': existing_title,
            'categories': self.category.id,
        })

        # Ensure that there's an error warning in the returned HTML content
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")
        self.assertIn("Goal with this Title already exists.", content)

        # Clean up.
        goal.delete()

    def test_author_post(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Goal.objects.get(pk=self.goal.id).title, 'A')

    def test_author_post_other_object(self):
        """Ensure authors cannot update someone else's content."""
        g = Goal.objects.create(title="Other", created_by=self.editor)
        self.client.login(username="author", password="pass")
        resp = self.client.post(g.get_update_url(), self.payload)
        self.assertEqual(resp.status_code, 403)
        g.delete()  # Clean up

    def test_viewer_post(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)


class TestGoalDeleteView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestGoalDeleteView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    def setUp(self):
        # Create a Goal
        self.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
            outcome="An Outcome"
        )
        self.url = self.goal.get_delete_url()

    def tearDown(self):
        Goal.objects.filter(id=self.goal.id).delete()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/goal_confirm_delete.html")
        self.assertIn("goal", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_anon_post(self):
        resp = self.ua_client.post(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_post(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("goals:index"))
        self.assertFalse(Goal.objects.filter(id=self.goal.id).exists())

    def test_editor_post(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("goals:index"))
        self.assertFalse(Goal.objects.filter(id=self.goal.id).exists())

    def test_author_post(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_post(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)


class TestTriggerListView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestTriggerListView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client
        cls.url = reverse("goals:trigger-list")

    @classmethod
    def setUpTestData(cls):
        super(cls, TestTriggerListView).setUpTestData()
        # Create Trigger
        cls.trigger = Trigger.objects.create(
            name="Test Trigger",
            trigger_type="time",
            time=time(13, 30, tzinfo=pytz.UTC),
            recurrences='RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR'
        )

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/trigger_list.html")
        self.assertIn("triggers", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)


class TestTriggerDetailView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestTriggerDetailView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestTriggerDetailView).setUpTestData()
        # Create a Trigger
        cls.trigger = Trigger.objects.create(
            name="Test Trigger",
            trigger_type="time",
            time=time(13, 30, tzinfo=pytz.UTC),
            recurrences='RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR'
        )
        cls.url = cls.trigger.get_absolute_url()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/trigger_detail.html")
        self.assertContains(resp, self.trigger.name)
        self.assertIn("trigger", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)


class TestTriggerCreateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestTriggerCreateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client
        cls.url = reverse("goals:trigger-create")
        cls.non_recurring_payload = {
            'name': "Test Trigger",
            'trigger_type': "time",
            'time': "",
            'recurrences': "",
        }

        cls.recurring_payload = {
            'name': "Recurring",
            'trigger_type': "time",
            'time': "13:30",
            'recurrences': 'RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR',
        }

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/trigger_form.html")
        self.assertIn("triggers", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_anon_post(self):
        resp = self.ua_client.post(self.url, {})
        self.assertEqual(resp.status_code, 403)

    def test_admin_post(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, self.non_recurring_payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Trigger.objects.default(name="Test Trigger").exists())

        resp = self.client.post(self.url, self.recurring_payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Trigger.objects.default(name="Recurring").exists())

    def test_editor_post(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, self.non_recurring_payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Trigger.objects.default(name="Test Trigger").exists())

        resp = self.client.post(self.url, self.recurring_payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Trigger.objects.default(name="Recurring").exists())

    def test_author_post(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, 403)

    def test_viewer_post(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, 403)


class TestTriggerUpdateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestTriggerUpdateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    def setUp(self):
        """NOTE: needs a new trigger for every test."""
        # Create a Trigger
        self.trigger = Trigger.objects.create(
            name="Test Trigger",
            trigger_type="time",
            time=time(13, 30, tzinfo=pytz.UTC),
            recurrences='RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR'
        )
        self.url = self.trigger.get_update_url()
        self.payload = {
            "name": "Changed",
            "trigger_type": self.trigger.trigger_type,
            "time": "13:30",
            "recurrences": 'RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR',
        }

    def tearDown(self):
        Trigger.objects.default(pk=self.trigger.id).delete()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/trigger_form.html")
        self.assertContains(resp, self.trigger.name)
        self.assertIn("triggers", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_anon_post(self):
        resp = self.ua_client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)

    def test_admin_post(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Trigger.objects.default(name="Changed").exists())

    def test_editor_post(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Trigger.objects.default(name="Changed").exists())

    def test_author_post(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_post(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)


class TestTriggerDeleteView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestTriggerDeleteView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    def setUp(self):
        """NOTE: need a new Trigger so we can delete it."""
        # Create a Trigger
        self.trigger = Trigger.objects.create(
            name="Test Trigger",
            trigger_type="time",
            time=time(13, 30, tzinfo=pytz.UTC),
            recurrences='RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR'
        )
        self.url = self.trigger.get_delete_url()

    def tearDown(self):
        Trigger.objects.default(id=self.trigger.id).delete()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/trigger_confirm_delete.html")
        self.assertIn("trigger", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_anon_post(self):
        resp = self.ua_client.post(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_post(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("goals:index"))

    def test_editor_post(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("goals:index"))

    def test_author_post(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_post(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)


class TestBehaviorListView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestBehaviorListView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client
        cls.url = reverse("goals:behavior-list")

    @classmethod
    def setUpTestData(cls):
        super(cls, TestBehaviorListView).setUpTestData()
        # Create Behavior
        cls.behavior = Behavior.objects.create(title="Test Behavior")

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behavior_list.html")
        self.assertIn("behaviors", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)


class TestBehaviorDetailView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestBehaviorDetailView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestBehaviorDetailView).setUpTestData()
        # Create Behavior
        cls.behavior = Behavior.objects.create(title="Test Behavior")
        cls.url = cls.behavior.get_absolute_url()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behavior_detail.html")
        self.assertContains(resp, self.behavior.title)
        self.assertIn("behavior", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)


class TestBehaviorCreateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestBehaviorCreateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client
        cls.url = reverse("goals:behavior-create")

    @classmethod
    def setUpTestData(cls):
        super(cls, TestBehaviorCreateView).setUpTestData()
        # Create a Goal to be used as an FK
        cls.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
            outcome="An Outcome"
        )
        cls.trigger = Trigger.objects.create(
            name=DEFAULT_BEHAVIOR_TRIGGER_NAME,
            trigger_type="time"
        )
        cls.payload = {'title': 'New', 'goals': cls.goal.id}

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behavior_form.html")
        self.assertIn("behaviors", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_anon_post(self):
        resp = self.ua_client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)

    def test_admin_post(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Behavior.objects.filter(title="New").exists())

    def test_editor_post(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Behavior.objects.filter(title="New").exists())

    def test_author_post(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Behavior.objects.filter(title="New").exists())

    def test_viewer_post(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)


class TestBehaviorDuplicateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestBehaviorDuplicateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestBehaviorDuplicateView).setUpTestData()
        cls.trigger = Trigger.objects.create(
            name=DEFAULT_BEHAVIOR_TRIGGER_NAME,
            trigger_type="time"
        )
        cls.behavior = Behavior.objects.create(title="Test Behavior")
        cls.url = cls.behavior.get_duplicate_url()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behavior_form.html")
        title_copy = "Copy of {0}".format(self.behavior.title)
        self.assertContains(resp, title_copy)
        self.assertIn("behaviors", resp.context)


class TestBehaviorPublishView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestBehaviorPublishView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestBehaviorPublishView).setUpTestData()
        # Create Behavior
        cls.behavior = Behavior.objects.create(title="Test Behavior")
        cls.url = cls.behavior.get_publish_url()

    def setUp(self):
        self.behavior.review()
        self.behavior.save()

    def tearDown(self):
        self.behavior.draft()
        self.behavior.save()

    def test_anon_publish(self):
        resp = self.ua_client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_admin_publish(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 302)
        state = Behavior.objects.get(pk=self.behavior.pk).state
        self.assertEqual(state, "published")

    def test_editor_publish(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 302)
        state = Behavior.objects.get(pk=self.behavior.pk).state
        self.assertEqual(state, "published")

    def test_author_publish(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_viewer_publish(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_anon_decline(self):
        resp = self.ua_client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_admin_decline(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 302)
        state = Behavior.objects.get(pk=self.behavior.pk).state
        self.assertEqual(state, "declined")

    def test_editor_decline(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 302)
        state = Behavior.objects.get(pk=self.behavior.pk).state
        self.assertEqual(state, "declined")

    def test_author_decline(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_viewer_decline(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 403)


class TestBehaviorUpdateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestBehaviorUpdateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestBehaviorUpdateView).setUpTestData()
        # Create a Goal
        cls.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
            outcome="An Outcome"
        )
        cls.trigger = Trigger.objects.create(
            name=DEFAULT_BEHAVIOR_TRIGGER_NAME,
            trigger_type="time"
        )
        cls.payload = {'title': 'U', 'goals': cls.goal.id}

    def setUp(self):
        # Re-create the behavior
        self.behavior = Behavior.objects.create(
            title="Title for Test Behavior",
            description="A Description",
            outcome="An Outcome",
            created_by=self.author
        )
        self.behavior.goals.add(self.goal)
        self.behavior.save()
        self.url = self.behavior.get_update_url()

    def tearDown(self):
        Behavior.objects.filter(id=self.behavior.id).delete()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behavior_form.html")
        self.assertContains(resp, self.behavior.title)
        self.assertIn("behaviors", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get_other_object(self):
        """Ensure authors cannot update someone else's content."""
        b = Behavior.objects.create(title="Other", created_by=self.editor)
        self.client.login(username="author", password="pass")
        resp = self.client.get(b.get_update_url())
        self.assertEqual(resp.status_code, 403)
        b.delete()  # Clean up

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_anon_post(self):
        resp = self.ua_client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)

    def test_admin_post(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Behavior.objects.get(id=self.behavior.id).title, "U")

    def test_editor_post(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Behavior.objects.get(id=self.behavior.id).title, "U")

    def test_editor_post_duplicate_title(self):
        """If you change the title of an existing object to somethign that
        would be a duplicate, the form should warn you (200 response) instead
        of throwing a 500 IntegrityError."""

        existing_title = "Title for Test Behavior"  # A pre-existing title.
        behavior = Behavior.objects.create(
            title="Some Behavior to Edit",
            created_by=self.editor
        )
        behavior.goals.add(self.goal)
        behavior.save()

        self.client.login(username="editor", password="pass")
        resp = self.client.post(behavior.get_update_url(), {
            'title': existing_title,
            'goals': self.goal.id,
        })

        # Ensure that we can an error warning in the returned HTML content
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")
        self.assertIn("Behavior with this Title already exists.", content)

        qs = Behavior.objects.filter(title=existing_title)
        self.assertEqual(qs.count(), 1)

        # Clean up.
        behavior.delete()

    def test_author_post(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Behavior.objects.get(id=self.behavior.id).title, "U")

    def test_author_post_other_object(self):
        """Ensure authors cannot update someone else's content."""
        b = Behavior.objects.create(title="Other", created_by=self.editor)
        self.client.login(username="author", password="pass")
        resp = self.client.post(b.get_update_url(), self.payload)
        self.assertEqual(resp.status_code, 403)
        b.delete()  # Clean up

    def test_viewer_post(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)


class TestBehaviorDeleteView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestBehaviorDeleteView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    def setUp(self):
        # Create a Behavior
        self.behavior = Behavior.objects.create(title="Test Behavior")
        self.url = self.behavior.get_delete_url()

    def tearDown(self):
        Behavior.objects.filter(id=self.behavior.id).delete()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behavior_confirm_delete.html")
        self.assertIn("behavior", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_anon_post(self):
        resp = self.ua_client.post(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_post(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("goals:index"))

    def test_editor_post(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("goals:index"))

    def test_author_post(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_post(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)


class TestActionListView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestActionListView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client
        cls.url = reverse("goals:action-list")

    @classmethod
    def setUpTestData(cls):
        super(cls, TestActionListView).setUpTestData()
        cls.behavior = Behavior.objects.create(title='Test Behavior')
        cls.action = Action.objects.create(
            behavior=cls.behavior,
            title="Test Action"
        )

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/action_list.html")
        self.assertIn("actions", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)


class TestActionDetailView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestActionDetailView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestActionDetailView).setUpTestData()
        # Create Behavior
        cls.behavior = Behavior.objects.create(title="Test Behavior")
        cls.action = Action.objects.create(
            behavior=cls.behavior,
            title="Test Action",
        )
        cls.url = cls.action.get_absolute_url()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/action_detail.html")
        self.assertContains(resp, self.action.title)
        self.assertIn("action", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)


class TestActionCreateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestActionCreateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client
        cls.url = reverse("goals:action-create")

    @classmethod
    def setUpTestData(cls):
        super(cls, TestActionCreateView).setUpTestData()
        # Create a Behavior to be used as an FK
        cls.behavior = Behavior.objects.create(title="Test Behavior")
        cls.payload = {
            'sequence_order': 1,
            'title': 'New',
            'behavior': cls.behavior.id,
            'action_type': Action.CUSTOM,
            'trigger-time': '22:00',
            'trigger-trigger_date': '08/20/2015',
            'trigger-recurrences': 'RRULE:FREQ=WEEKLY;BYDAY=SA',
        }

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/action_form.html")
        self.assertIn("actions", resp.context)
        self.assertIn("behaviors", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_anon_post(self):
        resp = self.ua_client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)

    def test_admin_post_empty_form(self):
        """This is an edge case, but it shouldn't cause a 500"""
        data = {
            'sequence_order': 0,
            'title': '',
            'behavior': '',
            'action_type': '',
            'trigger-time': '',
            'trigger-trigger_date': '',
            'trigger-recurrences': '',
        }
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)

    def test_admin_post(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Action.objects.filter(title="New").exists())

    def test_editor_post(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Action.objects.filter(title="New").exists())

    def test_author_post(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Action.objects.filter(title="New").exists())

    def test_viewer_post(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)


class TestActionDuplicateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestActionDuplicateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestActionDuplicateView).setUpTestData()
        cls.behavior = Behavior.objects.create(title="Test Behavior")
        cls.action = Action.objects.create(
            behavior=cls.behavior,
            title="Test Action",
        )
        cls.url = cls.action.get_duplicate_url()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/action_form.html")
        title_copy = "Copy of {0}".format(self.action.title)
        self.assertContains(resp, title_copy)
        self.assertIn("actions", resp.context)


class TestActionPublishView(TestCaseWithGroups):
    # TODO: need to include a test case for actions with duplicate titles/slugs

    @classmethod
    def setUpClass(cls):
        super(cls, TestActionPublishView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestActionPublishView).setUpTestData()
        # Create Behavior
        cls.behavior = Behavior.objects.create(title="Test Behavior")
        cls.action = Action.objects.create(
            behavior=cls.behavior,
            title="Test Action"
        )
        cls.url = cls.action.get_publish_url()

    def setUp(self):
        self.action.review()
        self.action.save()

    def tearDown(self):
        self.action.draft()
        self.action.save()

    def test_anon_publish(self):
        resp = self.ua_client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_admin_publish(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 302)
        state = Action.objects.get(pk=self.action.pk).state
        self.assertEqual(state, "published")

    def test_editor_publish(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 302)
        state = Action.objects.get(pk=self.action.pk).state
        self.assertEqual(state, "published")

    def test_author_publish(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_viewer_publish(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_anon_decline(self):
        resp = self.ua_client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_admin_decline(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 302)
        state = Action.objects.get(pk=self.action.pk).state
        self.assertEqual(state, "declined")

    def test_editor_decline(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 302)
        state = Action.objects.get(pk=self.action.pk).state
        self.assertEqual(state, "declined")

    def test_author_decline(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_viewer_decline(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 403)


class TestActionUpdateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestActionUpdateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestActionUpdateView).setUpTestData()
        cls.behavior = Behavior.objects.create(title='Test Behavior')
        cls.payload = {
            'sequence_order': 1,
            'title': 'U',
            'behavior': cls.behavior.id,
            'action_type': Action.CUSTOM,
            'trigger-time': '22:00',
            'trigger-trigger_date': '08/20/2015',
            'trigger-recurrences': 'RRULE:FREQ=WEEKLY;BYDAY=SA',
        }

    def setUp(self):
        # Re-create the Action
        self.action = Action.objects.create(
            behavior=self.behavior,
            title="Test Action",
            sequence_order=1,
            created_by=self.author
        )
        self.url = self.action.get_update_url()

    def tearDown(self):
        Action.objects.filter(id=self.behavior.id).delete()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/action_form.html")
        self.assertContains(resp, self.action.title)
        self.assertIn("actions", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get_other_object(self):
        """Ensure authors cannot update someone else's content."""
        a = Action.objects.create(
            behavior=self.behavior,
            title="Other",
            sequence_order=2,
            created_by=self.editor
        )
        self.client.login(username="author", password="pass")
        resp = self.client.get(a.get_update_url())
        self.assertEqual(resp.status_code, 403)
        a.delete()  # Clean up

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_anon_post(self):
        resp = self.ua_client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)

    def test_admin_post(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Action.objects.get(pk=self.action.pk).title, "U")

    def test_editor_post(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Action.objects.get(pk=self.action.pk).title, "U")

    def test_author_post(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Action.objects.get(pk=self.action.pk).title, "U")

    def test_author_post_other_object(self):
        """Ensure authors cannot update someone else's content."""
        a = Action.objects.create(
            behavior=self.behavior,
            title="Other",
            sequence_order=2,
            created_by=self.editor
        )
        self.client.login(username="author", password="pass")
        resp = self.client.post(a.get_update_url(), self.payload)
        self.assertEqual(resp.status_code, 403)
        a.delete()  # Clean up

    def test_viewer_post(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)


class TestActionDeleteView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestActionDeleteView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestActionDeleteView).setUpTestData()
        cls.behavior = Behavior.objects.create(title='Test Behavior')

    def setUp(self):
        # Create an Action
        self.action = Action.objects.create(
            behavior=self.behavior,
            title="Test Action",
        )
        self.url = self.action.get_delete_url()

    def tearDown(self):
        Action.objects.filter(id=self.action.id).delete()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/action_confirm_delete.html")
        self.assertIn("action", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_anon_post(self):
        resp = self.ua_client.post(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_post(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("goals:index"))

    def test_editor_post(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("goals:index"))

    def test_author_post(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_post(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)


class TestPackageEnrollmentView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # Create a contributor for the class.
        content_author_group = get_or_create_content_authors()
        args = ("contributor", "contributor@example.com", "pass")
        cls.contributor = User.objects.create_user(*args)
        cls.contributor.groups.add(content_author_group)

        # Create the Category and the content hierarchy
        cls.category = Category.objects.create(
            packaged_content=True,
            order=25,
            title="Test Package Category",
            state="published",
            created_by=cls.editor,
        )
        cls.category.package_contributors.add(cls.contributor)
        cls.category.save()

        cls.goal_a = Goal.objects.create(title="Pkg Goal A", state="published")
        cls.goal_b = Goal.objects.create(title="Pkg Goal B", state="published")
        cls.goal_a.categories.add(cls.category)
        cls.goal_b.categories.add(cls.category)

        cls.behavior_a = Behavior.objects.create(title='BA', state="published")
        cls.behavior_a.goals.add(cls.goal_a)
        cls.behavior_b = Behavior.objects.create(title='BB', state="published")
        cls.behavior_b.goals.add(cls.goal_b)

        cls.action_a = Action.objects.create(
            behavior=cls.behavior_a,
            title="Pkg Action A",
            state="published"
        )
        cls.action_b = Action.objects.create(
            behavior=cls.behavior_b,
            title="Pkg Action B",
            state="published"
        )

        # URL and POST payload
        cls.payload = {
            'email_addresses': 'new-user@example.com',
            'packaged_goals': [cls.goal_a.id],
        }
        cls.url = cls.category.get_enroll_url()
        cls.success_url = cls.category.get_view_enrollment_url()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/package_enroll.html")
        self.assertIn("category", resp.context)
        self.assertIn("form", resp.context)

    def test_contributor_get(self):
        self.client.login(username="contributor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("category", resp.context)
        self.assertIn("form", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("category", resp.context)
        self.assertIn("form", resp.context)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("category", resp.context)
        self.assertIn("form", resp.context)
        self.assertIsNone(resp.context['form'])

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_anon_post(self):
        resp = self.ua_client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)

    def test_admin_post(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, self.success_url)

    def test_editor_post(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, self.success_url)

    def test_author_post(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_post(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)


class TestAcceptEnrollmentCompleteView(TestCase):
    """Simple, publicly-available template."""

    def test_get(self):
        resp = self.client.get(reverse("accept-enrollment-complete"))
        self.assertEqual(resp.status_code, 200)
        self.client.logout()
