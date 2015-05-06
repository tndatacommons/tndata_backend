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
    get_or_create_content_editors,
    get_or_create_content_authors,
    get_or_create_content_viewers,
)
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

        args = ("admin", "admin@example.com", "pass")
        cls.admin = User.objects.create_superuser(*args)

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
            outcome="An Outcome"
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
        self.assertEqual(Goal.objects.get(pk=self.goal.id).title, 'A')

    def test_editor_post(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Goal.objects.get(pk=self.goal.id).title, 'A')

    def test_author_post(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Goal.objects.get(pk=self.goal.id).title, 'A')

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
            frequency="one-time",
            time="13:30",
            date="2014-02-01",
            text="Testing",
            instruction="Help"
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
            frequency="one-time",
            time="13:30",
            date="2014-02-01",
            text="Testing",
            instruction="Help"
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
        cls.payload = {
            'name': "Test Trigger",
            'trigger_type': "time",
            'frequency': "one-time",
            'time': "13:30",
            'date': "2014-02-01",
            'text': "Testing",
            'instruction': "Help",
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
        resp = self.ua_client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)

    def test_admin_post(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Trigger.objects.filter(name="Test Trigger").exists())

    def test_editor_post(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Trigger.objects.filter(name="Test Trigger").exists())

    def test_author_post(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_post(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)


class TestTriggerUpdateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestTriggerUpdateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    def setUp(self):
        # Create a Trigger
        self.trigger = Trigger.objects.create(
            name="Test Trigger",
            trigger_type="time",
            frequency="one-time",
            time="13:30",
            date="2014-02-01",
            text="Testing",
            instruction="Help"
        )
        self.url = self.trigger.get_update_url()
        self.payload = {'name': "Changed"}

    def tearDown(self):
        Trigger.objects.filter(id=self.trigger.id).delete()

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
        self.assertTrue(Trigger.objects.filter(name="Changed").exists())

    def test_editor_post(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Trigger.objects.filter(name="Changed").exists())

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
        # Create a Trigger
        self.trigger = Trigger.objects.create(
            name="Test Trigger",
            trigger_type="time",
            frequency="one-time",
            time="13:30",
            date="2014-02-01",
            text="Testing",
            instruction="Help"
        )
        self.url = self.trigger.get_delete_url()

    def tearDown(self):
        Trigger.objects.filter(id=self.trigger.id).delete()

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
        cls.payload = {'title': 'U', 'goals': cls.goal.id}

    def setUp(self):
        # Re-create the behavior
        self.behavior = Behavior.objects.create(
            title="Title for Test Behavior",
            description="A Description",
            outcome="An Outcome"
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

    def test_author_post(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Behavior.objects.get(id=self.behavior.id).title, "U")

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

    def test_admin_post(self):
        from clog.clog import clog
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, self.payload)
        if resp.status_code == 200:
            clog(resp.context_data['form'].errors, color="magenta")
            clog(resp.context_data['form'].data)
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


class TestActionPublishView(TestCaseWithGroups):

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
            'behavior': cls.behavior.id
        }

    def setUp(self):
        # Re-create the Action
        self.action = Action.objects.create(
            behavior=self.behavior,
            title="Test Action",
            sequence_order=1
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
