from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import Client, TestCase

from .. models import (
    Category,
    Goal,
    Trigger,
    BehaviorSequence,
    BehaviorAction,
)


class TestIndexView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()

    def test_get(self):
        url = reverse("goals:index")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestCategoryListView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Category
        self.category = Category.objects.create(
            order=1,
            name='Test Category',
            description='Some explanation!',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        Category.objects.filter(id=self.category.id).delete()

    def test_get(self):
        url = reverse("goals:category-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_list.html")
        self.assertIn("categories", resp.context)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestCategoryDetailView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Category
        self.category = Category.objects.create(
            order=1,
            name='Test Category',
            description='Some explanation!',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        Category.objects.filter(id=self.category.id).delete()

    def test_get(self):
        url = self.category.get_absolute_url()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_detail.html")
        self.assertContains(resp, self.category.name)
        self.assertIn("category", resp.context)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestCategoryCreateView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Category
        self.category = Category.objects.create(
            order=1,
            name='Test Category',
            description='Some explanation!',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        Category.objects.filter(id=self.category.id).delete()

    def test_get(self):
        url = reverse("goals:category-create")

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_form.html")
        self.assertContains(resp, self.category.name)
        self.assertIn("categories", resp.context)


class TestCategoryUpdateView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Category
        self.category = Category.objects.create(
            order=1,
            name='Test Category',
            description='Some explanation!',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        Category.objects.filter(id=self.category.id).delete()

    def test_get(self):
        url = self.category.get_update_url()

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_form.html")
        self.assertContains(resp, self.category.name)
        self.assertIn("categories", resp.context)


class TestCategoryDeleteView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a Category
        self.category = Category.objects.create(
            order=1,
            name='Test Category',
            description='Some explanation!',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        Category.objects.filter(id=self.category.id).delete()

    def test_get(self):
        url = self.category.get_delete_url()
        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_confirm_delete.html")
        self.assertIn("category", resp.context)

    def test_post(self):
        url = self.category.get_delete_url()
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse("goals:index"))


class TestGoalListView(TestCase):

    def setUp(self):
        User = get_user_model()
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

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        Goal.objects.filter(id=self.goal.id).delete()

    def test_get(self):
        url = reverse("goals:goal-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/goal_list.html")
        self.assertIn("goals", resp.context)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestGoalDetailView(TestCase):

    def setUp(self):
        User = get_user_model()
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

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        Goal.objects.filter(id=self.goal.id).delete()

    def test_get(self):
        url = self.goal.get_absolute_url()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/goal_detail.html")
        self.assertContains(resp, self.goal.title)
        self.assertIn("goal", resp.context)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestGoalCreateView(TestCase):

    def setUp(self):
        User = get_user_model()
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

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        Goal.objects.filter(id=self.goal.id).delete()

    def test_get(self):
        url = reverse("goals:goal-create")

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/goal_form.html")
        self.assertContains(resp, self.goal.title)
        self.assertIn("goals", resp.context)


class TestGoalUpdateView(TestCase):

    def setUp(self):
        User = get_user_model()
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

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        Goal.objects.filter(id=self.goal.id).delete()

    def test_get(self):
        url = self.goal.get_update_url()

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/goal_form.html")
        self.assertContains(resp, self.goal.title)
        self.assertIn("goals", resp.context)


class TestGoalDeleteView(TestCase):

    def setUp(self):
        User = get_user_model()
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

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        Goal.objects.filter(id=self.goal.id).delete()

    def test_get(self):
        url = self.goal.get_delete_url()
        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/goal_confirm_delete.html")
        self.assertIn("goal", resp.context)

    def test_post(self):
        url = self.goal.get_delete_url()
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse("goals:index"))


class TestTriggerListView(TestCase):

    def setUp(self):
        User = get_user_model()
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

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        Trigger.objects.filter(id=self.trigger.id).delete()

    def test_get(self):
        url = reverse("goals:trigger-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/trigger_list.html")
        self.assertIn("triggers", resp.context)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestTriggerDetailView(TestCase):

    def setUp(self):
        User = get_user_model()
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

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        Trigger.objects.filter(id=self.trigger.id).delete()

    def test_get(self):
        url = self.trigger.get_absolute_url()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/trigger_detail.html")
        self.assertContains(resp, self.trigger.name)
        self.assertIn("trigger", resp.context)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestTriggerCreateView(TestCase):

    def setUp(self):
        User = get_user_model()
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

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        Trigger.objects.filter(id=self.trigger.id).delete()

    def test_get(self):
        url = reverse("goals:trigger-create")

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/trigger_form.html")
        self.assertContains(resp, self.trigger.name)
        self.assertIn("triggers", resp.context)


class TestTriggerUpdateView(TestCase):

    def setUp(self):
        User = get_user_model()
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

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        Trigger.objects.filter(id=self.trigger.id).delete()

    def test_get(self):
        url = self.trigger.get_update_url()

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/trigger_form.html")
        self.assertContains(resp, self.trigger.name)
        self.assertIn("triggers", resp.context)


class TestTriggerDeleteView(TestCase):

    def setUp(self):
        User = get_user_model()
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

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        Trigger.objects.filter(id=self.trigger.id).delete()

    def test_get(self):
        url = self.trigger.get_delete_url()
        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/trigger_confirm_delete.html")
        self.assertIn("trigger", resp.context)

    def test_post(self):
        url = self.trigger.get_delete_url()
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse("goals:index"))


class TestBehaviorSequenceListView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create BehaviorSequence
        self.bs = BehaviorSequence.objects.create(
            name="Test BehaviorSequence",
            title="Formal Title",
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        BehaviorSequence.objects.filter(id=self.bs.id).delete()

    def test_get(self):
        url = reverse("goals:behaviorsequence-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behaviorsequence_list.html")
        self.assertIn("behaviorsequences", resp.context)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestBehaviorSequenceDetailView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a BehaviorSequence
        self.bs = BehaviorSequence.objects.create(
            name="Test BehaviorSequence",
            title="Formal Title",
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        BehaviorSequence.objects.filter(id=self.bs.id).delete()

    def test_get(self):
        url = self.bs.get_absolute_url()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behaviorsequence_detail.html")
        self.assertContains(resp, self.bs.name)
        self.assertIn("behaviorsequence", resp.context)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestBehaviorSequenceCreateView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a BehaviorSequence
        self.bs = BehaviorSequence.objects.create(
            name="Test BehaviorSequence",
            title="Formal Title",
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        BehaviorSequence.objects.filter(id=self.bs.id).delete()

    def test_get(self):
        url = self.bs.get_absolute_url()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behaviorsequence_detail.html")
        self.assertContains(resp, self.bs.name)
        self.assertIn("behaviorsequence", resp.context)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestBehaviorSequenceUpdateView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a BehaviorSequence
        self.bs = BehaviorSequence.objects.create(
            name="Test BehaviorSequence",
            title="Formal Title"
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        BehaviorSequence.objects.filter(id=self.bs.id).delete()

    def test_get(self):
        url = self.bs.get_update_url()

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behaviorsequence_form.html")
        self.assertContains(resp, self.bs.name)
        self.assertIn("behaviorsequences", resp.context)


class TestBehaviorSequenceDeleteView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a BehaviorSequence
        self.bs = BehaviorSequence.objects.create(
            name="Test BehaviorSequence",
            title="Formal Title"
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        BehaviorSequence.objects.filter(id=self.bs.id).delete()

    def test_get(self):
        url = self.bs.get_delete_url()
        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behaviorsequence_confirm_delete.html")
        self.assertIn("behaviorsequence", resp.context)

    def test_post(self):
        url = self.bs.get_delete_url()
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse("goals:index"))


# ----------------------------------
class TestBehaviorActionListView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create BehaviorAction
        self.bs = BehaviorSequence.objects.create(
            name='Test BehaviorSequence',
            title="Formal Title",
        )
        self.ba = BehaviorAction.objects.create(
            sequence=self.bs,
            name="Test BehaviorAction",
            title="Formal Title",
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        BehaviorAction.objects.filter(id=self.ba.id).delete()
        BehaviorSequence.objects.filter(id=self.bs.id).delete()

    def test_get(self):
        url = reverse("goals:behavioraction-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behavioraction_list.html")
        self.assertIn("behavioractions", resp.context)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestBehaviorActionDetailView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a BehaviorAction
        self.bs = BehaviorSequence.objects.create(
            name='Test BehaviorSequence',
            title="Formal Title",
        )
        self.ba = BehaviorAction.objects.create(
            sequence=self.bs,
            name="Test BehaviorAction",
            title="Formal Title",
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        BehaviorAction.objects.filter(id=self.ba.id).delete()
        BehaviorSequence.objects.filter(id=self.bs.id).delete()

    def test_get(self):
        url = self.ba.get_absolute_url()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behavioraction_detail.html")
        self.assertContains(resp, self.ba.name)
        self.assertIn("behavioraction", resp.context)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestBehaviorActionCreateView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a BehaviorAction
        self.bs = BehaviorSequence.objects.create(
            name='Test BehaviorSequence',
            title="Formal Title",
        )
        self.ba = BehaviorAction.objects.create(
            sequence=self.bs,
            name="Test BehaviorAction",
            title="Formal Title",
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        BehaviorAction.objects.filter(id=self.ba.id).delete()
        BehaviorSequence.objects.filter(id=self.bs.id).delete()

    def test_get(self):
        url = self.ba.get_absolute_url()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behavioraction_detail.html")
        self.assertContains(resp, self.ba.name)
        self.assertIn("behavioraction", resp.context)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestBehaviorActionUpdateView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a BehaviorAction
        self.bs = BehaviorSequence.objects.create(
            name='Test BehaviorSequence',
            title="Formal Title",
        )
        self.ba = BehaviorAction.objects.create(
            sequence=self.bs,
            name="Test BehaviorAction",
            title="Formal Title",
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        BehaviorAction.objects.filter(id=self.ba.id).delete()
        BehaviorSequence.objects.filter(id=self.bs.id).delete()

    def test_get(self):
        url = self.ba.get_update_url()

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behavioraction_form.html")
        self.assertContains(resp, self.ba.name)
        self.assertIn("behavioractions", resp.context)


class TestBehaviorActionDeleteView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a BehaviorAction
        self.bs = BehaviorSequence.objects.create(
            name='Test BehaviorSequence',
            title="Formal Title",
        )
        self.ba = BehaviorAction.objects.create(
            sequence=self.bs,
            name="Test BehaviorAction",
            title="Formal Title",
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        BehaviorAction.objects.filter(id=self.ba.id).delete()
        BehaviorSequence.objects.filter(id=self.bs.id).delete()

    def test_get(self):
        url = self.ba.get_delete_url()
        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/behavioraction_confirm_delete.html")
        self.assertIn("behavioraction", resp.context)

    def test_post(self):
        url = self.ba.get_delete_url()
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse("goals:index"))
