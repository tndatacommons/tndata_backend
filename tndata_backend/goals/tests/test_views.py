from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
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
    CONTENT_AUTHORS,
    CONTENT_EDITORS,
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

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create Goal
        self.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
            outcome="An Outcome"
        )

        # The URL for this view
        self.url = reverse("goals:goal-list")

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Goal.objects.filter(id=self.goal.id).delete()

    def test_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/goal_list.html")
        self.assertIn("goals", resp.context)

        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()


class TestGoalDetailView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Goal
        self.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
            outcome="An Outcome"
        )

        # The URL for this view.
        self.url = self.goal.get_absolute_url()

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Goal.objects.filter(id=self.goal.id).delete()

    def test_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/goal_detail.html")
        self.assertContains(resp, self.goal.title)
        self.assertIn("goal", resp.context)

        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()


class TestGoalCreateView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Goal
        self.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
            outcome="An Outcome"
        )

        self.url = reverse("goals:goal-create")

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Goal.objects.filter(id=self.goal.id).delete()

    def test_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/goal_form.html")
        self.assertContains(resp, self.goal.title)
        self.assertIn("goals", resp.context)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()


class TestGoalPublishView(TestCaseWithGroups):

    def setUp(self):
        # Create author/editor in appropriate Groups.
        author_group = Group.objects.get(name=CONTENT_AUTHORS)
        self.author = User.objects.create_user("author", password="p")
        self.author.groups.add(author_group)

        editor_group = Group.objects.get(name=CONTENT_EDITORS)
        self.editor = User.objects.create_user("editor", password="p")
        self.editor.groups.add(editor_group)

        # Create a Goal under review
        self.goal = Goal.objects.create(
            title='Test Goal',
            description='Some explanation!',
            outcome="An Outcome",
            state="pending-review"
        )
        self.url = self.goal.get_publish_url()

    def tearDown(self):
        User.objects.filter(pk__in=[self.author.id, self.editor.id]).delete()
        Goal.objects.filter(id=self.goal.id).delete()
        self.client.logout()

    def test_publish_with_contentauthor(self):
        self.client.login(username="author", password="p")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Goal.objects.get(pk=self.goal.pk).state,
            "pending-review"  # Failed.
        )

    def test_decline_with_contentauthor(self):
        self.client.login(username="author", password="p")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Goal.objects.get(pk=self.goal.pk).state,
            "pending-review"
        )

    def test_publish_with_contenteditor(self):
        self.client.login(username="editor", password="p")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Goal.objects.get(pk=self.goal.pk).state,
            "published"
        )

    def test_decline_with_contenteditor(self):
        self.client.login(username="editor", password="p")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Goal.objects.get(pk=self.goal.pk).state,
            "declined"
        )


class TestGoalUpdateView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Goal
        self.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
            outcome="An Outcome"
        )
        self.url = self.goal.get_update_url()

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Goal.objects.filter(id=self.goal.id).delete()

    def test_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/goal_form.html")
        self.assertContains(resp, self.goal.title)
        self.assertIn("goals", resp.context)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()


class TestGoalDeleteView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create n Goal
        self.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
            outcome="An Outcome"
        )
        self.url = self.goal.get_delete_url()

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Goal.objects.filter(id=self.goal.id).delete()

    def test_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/goal_confirm_delete.html")
        self.assertIn("goal", resp.context)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)  # Not allowed
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()

    def test_post(self):
        resp = self.client.post(self.url)
        self.assertRedirects(resp, reverse("goals:index"))


class TestTriggerListView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create Trigger
        self.trigger = Trigger.objects.create(
            name="Test Trigger",
            trigger_type="time",
            frequency="one-time",
            time="13:30",
            date="2014-02-01",
            text="Testing",
            instruction="Help"
        )
        self.url = reverse("goals:trigger-list")

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Trigger.objects.filter(id=self.trigger.id).delete()

    def test_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/trigger_list.html")
        self.assertIn("triggers", resp.context)

        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()


class TestTriggerDetailView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

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
        self.url = self.trigger.get_absolute_url()

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Trigger.objects.filter(id=self.trigger.id).delete()

    def test_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/trigger_detail.html")
        self.assertContains(resp, self.trigger.name)
        self.assertIn("trigger", resp.context)

        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()


class TestTriggerCreateView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

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
        self.url = reverse("goals:trigger-create")

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Trigger.objects.filter(id=self.trigger.id).delete()

    def test_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/trigger_form.html")
        self.assertContains(resp, self.trigger.name)
        self.assertIn("triggers", resp.context)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)  # Not allowed
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()


class TestTriggerUpdateView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

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

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Trigger.objects.filter(id=self.trigger.id).delete()

    def test_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/trigger_form.html")
        self.assertContains(resp, self.trigger.name)
        self.assertIn("triggers", resp.context)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)  # Not allowed
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()


class TestTriggerDeleteView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

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
        User.objects.filter(username="admin").delete()
        Trigger.objects.filter(id=self.trigger.id).delete()

    def test_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/trigger_confirm_delete.html")
        self.assertIn("trigger", resp.context)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)  # Not allowed
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()

    def test_post(self):
        resp = self.client.post(self.url)
        self.assertRedirects(resp, reverse("goals:index"))


class TestBehaviorListView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create Behavior
        self.behavior = Behavior.objects.create(title="Test Behavior")
        self.url = reverse("goals:behavior-list")

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Behavior.objects.filter(id=self.behavior.id).delete()

    def test_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behavior_list.html")
        self.assertIn("behaviors", resp.context)

        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()


class TestBehaviorDetailView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Behavior
        self.behavior = Behavior.objects.create(title="Test Behavior")
        self.url = self.behavior.get_absolute_url()

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Behavior.objects.filter(id=self.behavior.id).delete()

    def test_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behavior_detail.html")
        self.assertContains(resp, self.behavior.title)
        self.assertIn("behavior", resp.context)

        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()


class TestBehaviorCreateView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Behavior
        self.behavior = Behavior.objects.create(title="Test Behavior")
        self.url = self.behavior.get_absolute_url()

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Behavior.objects.filter(id=self.behavior.id).delete()

    def test_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behavior_detail.html")
        self.assertContains(resp, self.behavior.title)
        self.assertIn("behavior", resp.context)

        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()


class TestBehaviorPublishView(TestCaseWithGroups):

    def setUp(self):
        # Create author/editor in appropriate Groups.
        author_group = Group.objects.get(name=CONTENT_AUTHORS)
        self.author = User.objects.create_user("author", password="p")
        self.author.groups.add(author_group)

        editor_group = Group.objects.get(name=CONTENT_EDITORS)
        self.editor = User.objects.create_user("editor", password="p")
        self.editor.groups.add(editor_group)

        # Create a Behavior under review
        self.behavior = Behavior.objects.create(
            title='Test Behavior',
            state="pending-review"
        )
        self.url = self.behavior.get_publish_url()

    def tearDown(self):
        User.objects.filter(pk__in=[self.author.id, self.editor.id]).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()
        self.client.logout()

    def test_publish_with_contentauthor(self):
        self.client.login(username="author", password="p")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Behavior.objects.get(pk=self.behavior.pk).state,
            "pending-review"  # Failed.
        )

    def test_decline_with_contentauthor(self):
        self.client.login(username="author", password="p")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Behavior.objects.get(pk=self.behavior.pk).state,
            "pending-review"
        )

    def test_publish_with_contenteditor(self):
        self.client.login(username="editor", password="p")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Behavior.objects.get(pk=self.behavior.pk).state,
            "published"
        )

    def test_decline_with_contenteditor(self):
        self.client.login(username="editor", password="p")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Behavior.objects.get(pk=self.behavior.pk).state,
            "declined"
        )


class TestBehaviorUpdateView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Behavior
        self.behavior = Behavior.objects.create(title="Test Behavior")
        self.url = self.behavior.get_update_url()

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Behavior.objects.filter(id=self.behavior.id).delete()

    def test_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behavior_form.html")
        self.assertContains(resp, self.behavior.title)
        self.assertIn("behaviors", resp.context)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()


class TestBehaviorDeleteView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Behavior
        self.behavior = Behavior.objects.create(title="Test Behavior")
        self.url = self.behavior.get_delete_url()

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Behavior.objects.filter(id=self.behavior.id).delete()

    def test_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behavior_confirm_delete.html")
        self.assertIn("behavior", resp.context)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)  # Not allowed
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()

    def test_post(self):
        url = self.behavior.get_delete_url()
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse("goals:index"))


class TestActionListView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create Action
        self.behavior = Behavior.objects.create(title='Test Behavior')
        self.action = Action.objects.create(
            behavior=self.behavior,
            title="Test Action"
        )
        self.url = reverse("goals:action-list")

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Action.objects.filter(id=self.action.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()

    def test_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/action_list.html")
        self.assertIn("actions", resp.context)

        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()


class TestActionDetailView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Action
        self.behavior = Behavior.objects.create(title='Test Behavior')
        self.action = Action.objects.create(
            behavior=self.behavior,
            title="Test Action",
        )
        self.url = self.action.get_absolute_url()

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Action.objects.filter(id=self.action.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()

    def test_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/action_detail.html")
        self.assertContains(resp, self.action.title)
        self.assertIn("action", resp.context)

        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()


class TestActionCreateView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Action
        self.behavior = Behavior.objects.create(title='Test Behavior')
        self.action = Action.objects.create(
            behavior=self.behavior,
            title="Test Action",
        )
        self.url = self.action.get_absolute_url()

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Action.objects.filter(id=self.action.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()

    def test_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/action_detail.html")
        self.assertContains(resp, self.action.title)
        self.assertIn("action", resp.context)

        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()


class TestActionPublishView(TestCaseWithGroups):

    def setUp(self):
        # Create author/editor in appropriate Groups.
        author_group = Group.objects.get(name=CONTENT_AUTHORS)
        self.author = User.objects.create_user("author", password="p")
        self.author.groups.add(author_group)

        editor_group = Group.objects.get(name=CONTENT_EDITORS)
        self.editor = User.objects.create_user("editor", password="p")
        self.editor.groups.add(editor_group)

        # Create a Action under review
        self.behavior = Behavior.objects.create(title='Test Behavior')
        self.action = Action.objects.create(
            behavior=self.behavior,
            title="Test Action",
            state="pending-review"
        )
        self.url = self.action.get_publish_url()

    def tearDown(self):
        User.objects.filter(pk__in=[self.author.id, self.editor.id]).delete()
        Action.objects.filter(id=self.action.id).delete()
        self.client.logout()

    def test_publish_with_contentauthor(self):
        self.client.login(username="author", password="p")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Action.objects.get(pk=self.action.pk).state,
            "pending-review"  # Failed.
        )

    def test_decline_with_contentauthor(self):
        self.client.login(username="author", password="p")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Action.objects.get(pk=self.action.pk).state,
            "pending-review"
        )

    def test_publish_with_contenteditor(self):
        self.client.login(username="editor", password="p")
        resp = self.client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Action.objects.get(pk=self.action.pk).state,
            "published"
        )

    def test_decline_with_contenteditor(self):
        self.client.login(username="editor", password="p")
        resp = self.client.post(self.url, {"decline": "1"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Action.objects.get(pk=self.action.pk).state,
            "declined"
        )


class TestActionUpdateView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Action
        self.behavior = Behavior.objects.create(title='Test Behavior')
        self.action = Action.objects.create(
            behavior=self.behavior,
            title="Test Action",
        )
        self.url = self.action.get_update_url()

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Action.objects.filter(id=self.action.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()

    def test_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/action_form.html")
        self.assertContains(resp, self.action.title)
        self.assertIn("actions", resp.context)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()


class TestActionDeleteView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.admin = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Action
        self.behavior = Behavior.objects.create(title='Test Behavior')
        self.action = Action.objects.create(
            behavior=self.behavior,
            title="Test Action",
        )
        self.url = self.action.get_delete_url()

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Action.objects.filter(id=self.action.id).delete()
        Behavior.objects.filter(id=self.behavior.id).delete()

    def test_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/action_confirm_delete.html")
        self.assertIn("action", resp.context)

    def test_get_with_contentauthor(self):
        group = Group.objects.get(name=CONTENT_AUTHORS)
        u = User.objects.create_user("author", password="p")
        u.groups.add(group)
        self.client.login(username="author", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)  # Not allowed
        u.delete()

    def test_get_with_contenteditor(self):
        group = Group.objects.get(name=CONTENT_EDITORS)
        u = User.objects.create_user("editor", password="p")
        u.groups.add(group)
        self.client.login(username="editor", password="p")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        u.delete()

    def test_post(self):
        resp = self.client.post(self.url)
        self.assertRedirects(resp, reverse("goals:index"))
