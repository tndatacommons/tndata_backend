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
)


User = get_user_model()


class TestCaseWithGroups(TestCase):
    """A TestCase Subclass that ensures we have appropriate Groups."""
    @classmethod
    def setUpClass(cls):
        super(TestCaseWithGroups, cls).setUpClass()
        get_or_create_content_editors()
        get_or_create_content_authors()


class TestIndexView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")
        self.url = reverse("goals:index")

    def tearDown(self):
        User.objects.filter(username="admin").delete()

    def test_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

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


class TestCategoryListView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Category
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )
        self.url = reverse("goals:category-list")

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Category.objects.filter(id=self.category.id).delete()

    def test_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_list.html")
        self.assertIn("categories", resp.context)

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


class TestCategoryDetailView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Category
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )
        self.url = self.category.get_absolute_url()

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Category.objects.filter(id=self.category.id).delete()

    def test_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_detail.html")
        self.assertContains(resp, self.category.title)
        self.assertIn("category", resp.context)

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


class TestCategoryCreateView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Category
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )
        self.url = reverse("goals:category-create")

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Category.objects.filter(id=self.category.id).delete()

    def test_get(self):

        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_form.html")
        self.assertContains(resp, self.category.title)
        self.assertIn("categories", resp.context)

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


class TestCategoryUpdateView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Category
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )
        self.url = self.category.get_update_url()

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Category.objects.filter(id=self.category.id).delete()

    def test_get(self):

        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_form.html")
        self.assertContains(resp, self.category.title)
        self.assertIn("categories", resp.context)

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


class TestCategoryDeleteView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Category
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )
        self.url = self.category.get_delete_url()

    def tearDown(self):
        User.objects.filter(username="admin").delete()
        Category.objects.filter(id=self.category.id).delete()

    def test_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_confirm_delete.html")
        self.assertIn("category", resp.context)

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
        url = self.category.get_delete_url()
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse("goals:index"))


class TestGoalListView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

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
        self.user = User.objects.create_superuser(*user_args)

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
        self.user = User.objects.create_superuser(*user_args)

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


class TestGoalUpdateView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

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
        self.user = User.objects.create_superuser(*user_args)

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
        self.user = User.objects.create_superuser(*user_args)

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
        self.user = User.objects.create_superuser(*user_args)

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
        self.user = User.objects.create_superuser(*user_args)

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
        self.user = User.objects.create_superuser(*user_args)

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
        self.user = User.objects.create_superuser(*user_args)

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
        self.user = User.objects.create_superuser(*user_args)

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
        self.user = User.objects.create_superuser(*user_args)

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
        self.user = User.objects.create_superuser(*user_args)

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


class TestBehaviorUpdateView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

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
        self.user = User.objects.create_superuser(*user_args)

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
        self.user = User.objects.create_superuser(*user_args)

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
        self.user = User.objects.create_superuser(*user_args)

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
        self.user = User.objects.create_superuser(*user_args)

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


class TestActionUpdateView(TestCaseWithGroups):

    def setUp(self):
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

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
        self.user = User.objects.create_superuser(*user_args)

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
