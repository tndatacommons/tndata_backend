from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse
from django.test import Client, TestCase, override_settings
from django_rq import get_worker
from model_mommy import mommy

from .. models import (
    Action,
    Category,
    Goal,
    Organization,
    Program,
    PackageEnrollment,
)
from .. permissions import (
    ContentPermissions,
    Group,
    get_or_create_content_admins,
    get_or_create_content_editors,
    get_or_create_content_authors,
    get_or_create_content_viewers,
    CONTENT_ADMINS,
    CONTENT_AUTHORS,
    CONTENT_EDITORS,
    CONTENT_VIEWERS,
)


TEST_SESSION_ENGINE = 'django.contrib.sessions.backends.db'
TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
TEST_RQ_QUEUES = settings.RQ_QUEUES.copy()
TEST_RQ_QUEUES['default']['ASYNC'] = False


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestPermissions(TestCase):

    def setUp(self):
        Group.objects.all().delete()

    def tearDown(self):
        Group.objects.all().delete()

    def test_get_or_create_content_admins(self):
        group = get_or_create_content_admins()
        self.assertEqual(group.name, CONTENT_ADMINS)
        perms = ["goals.{}".format(p.codename) for p in group.permissions.all()]
        self.assertEqual(sorted(perms), sorted(ContentPermissions.admins))

        expected_codenames = [
            'add_action',
            'add_category',
            'add_goal',
            'add_trigger',
            'change_action',
            'change_category',
            'change_goal',
            'change_trigger',
            'decline_action',
            'decline_category',
            'decline_goal',
            'decline_trigger',
            'delete_action',
            'delete_category',
            'delete_goal',
            'delete_trigger',
            'publish_action',
            'publish_category',
            'publish_goal',
            'publish_trigger',
            'view_action',
            'view_category',
            'view_goal',
            'view_trigger'
        ]
        codenames = sorted(ContentPermissions.admin_codenames)
        self.assertEqual(codenames, expected_codenames)

    def test_get_or_create_content_editors(self):
        group = get_or_create_content_editors()
        self.assertEqual(group.name, CONTENT_EDITORS)
        perms = ["goals.{}".format(p.codename) for p in group.permissions.all()]

        self.assertEqual(sorted(perms), sorted(ContentPermissions.editors))

        expected_codenames = [
            'add_action',
            'add_goal',
            'change_action',
            'change_goal',
            'decline_action',
            'decline_goal',
            'delete_action',
            'delete_goal',
            'publish_action',
            'publish_goal',
            'view_action',
            'view_category',
            'view_goal',
        ]

        codenames = sorted(ContentPermissions.editor_codenames)
        self.assertEqual(codenames, expected_codenames)

    def test_get_or_create_content_authors(self):
        group = get_or_create_content_authors()
        self.assertEqual(group.name, CONTENT_AUTHORS)
        perms = ["goals.{}".format(p.codename) for p in group.permissions.all()]
        self.assertEqual(sorted(perms), sorted(ContentPermissions.authors))

        expected_codenames = [
            'add_action',
            'add_goal',
            'change_action',
            'change_goal',
            'view_action',
            'view_category',
            'view_goal'
        ]
        codenames = sorted(ContentPermissions.author_codenames)
        self.assertEqual(codenames, expected_codenames)

    def test_get_or_create_content_viewers(self):
        group = get_or_create_content_viewers()
        self.assertEqual(group.name, CONTENT_VIEWERS)
        perms = ["goals.{}".format(p.codename) for p in group.permissions.all()]
        self.assertEqual(sorted(perms), sorted(ContentPermissions.viewers))

        expected_codenames = [
            'view_action', 'view_category', 'view_goal'
        ]
        codenames = sorted(ContentPermissions.viewer_codenames)
        self.assertEqual(codenames, expected_codenames)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
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
        User = get_user_model()
        Group.objects.all().delete()

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


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
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
        self.assertEqual(resp.status_code, 302)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestMyContentView(TestCaseWithGroups):
    # NOTE: tests are named with this convention:
    # test_[auth-group]_[http-verb]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client
        cls.url = reverse("goals:my-content")

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
        self.assertEqual(resp.status_code, 302)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
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
        self.assertEqual(resp.status_code, 302)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
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
        self.assertEqual(resp.status_code, 302)

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

    def test_viewer_get_changed_url(self):
        """Ensure we can still access a page if the title_slug changes."""
        self.client.login(username="viewer", password="pass")

        # if the object's title changes, the old url should still work.
        self.category.title = "Some New thing that's different"
        self.category.save()
        self.assertNotEqual(self.category.get_absolute_url(), self.url)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
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
        cls.payload = {
            'packaged_content': False,
            'contributors': '',
            'order': 2,
            'title': 'New',
            'description': 'Desc',
            'color': '#f00',
        }

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_form.html")

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_form.html")

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
        self.assertEqual(resp.status_code, 302)

    def test_admin_post(self):
        """Ensure Admins can create new Categories"""
        self.client.login(username="admin", password="pass")
        payload = {'order': 2, 'title': 'New', 'description': 'Desc', 'color': '#f00'}
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Category.objects.filter(title="New").exists())

        # Ensure we redirect to the detail page afterwards
        new_cat = Category.objects.get(title="New")
        self.assertIn(new_cat.get_absolute_url(), resp.get('Location', ''))

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


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
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
        self.assertEqual(resp.status_code, 302)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_form.html")
        title_copy = "Copy of {0}".format(self.category.title)
        self.assertContains(resp, title_copy)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
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
        self.assertEqual(resp.status_code, 302)

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
        self.assertEqual(resp.status_code, 302)

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


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestCategoryUpdateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestCategoryUpdateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client
        cls.payload = {
            'order': 1,
            'title': 'Test Category',
            'description': 'Some explanation!',
            'color': '#ff0000',
        }

    def setUp(self):
        # Define a user that will be a package contributor.
        User = get_user_model()
        args = ("contrib", "contrib@example.com", "pass")
        self.contributor = User.objects.create_user(*args)
        content_viewer_group = get_or_create_content_viewers()
        self.contributor.groups.add(content_viewer_group)

        # Create a Category
        self.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )
        self.category.contributors.add(self.contributor)
        self.url = self.category.get_update_url()

    def tearDown(self):
        Category.objects.filter(id=self.category.id).delete()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_admin_get(self):
        resp = self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/category_form.html")
        self.assertContains(resp, self.category.title)

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

    def test_contributor_get(self):
        resp = self.client.login(username="contrib", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_other_contributor_get(self):
        """When a user is a contributor for another category, they should't be
        able to update this view."""
        User = get_user_model()
        user = User.objects.create_user("x", "x@x.x", "xxx")
        content_viewer_group = get_or_create_content_viewers()
        user.groups.add(content_viewer_group)

        cat = Category.objects.create(order=2, title="x")
        cat.contributors.add(user)

        resp = self.client.login(username="x", password="xxx")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

        cat.delete()
        user.delete()

    def test_redirect_after_save(self):
        """Ensure we redirect to the detail page after saving"""
        self.assertEqual(self.category.state, "draft")  # Ensure we start as draft
        payload = self.payload.copy()
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, payload)
        self.assertIn(self.category.get_absolute_url(), resp.get("Location", ''))
        self.assertEqual(resp.status_code, 302)

    def test_viewer_submit_for_review(self):
        """Ensure viewers cannot submit for review."""
        self.assertEqual(self.category.state, "draft")  # Ensure we start as draft
        payload = self.payload.copy()
        payload['review'] = 1
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 403)

    def test_editor_submit_for_review(self):
        """Ensure editors can submit for review."""
        self.assertEqual(self.category.state, "draft")  # Ensure we start as draft
        payload = self.payload.copy()
        payload['review'] = 1  # Include the review in the payload
        self.client.login(username="editor", password="pass")

        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Category.objects.get(pk=self.category.pk).state, "pending-review")

    def test_admin_submit_for_review(self):
        """Ensure admins can submit for review."""
        self.assertEqual(self.category.state, "draft")  # Ensure we start as draft
        payload = self.payload.copy()
        payload['review'] = 1  # Include the review in the payload
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Category.objects.get(pk=self.category.pk).state, "pending-review")

    def test_author_submit_for_review(self):
        """Ensure authors CANNOT submit for review (not on Categories)"""
        self.assertEqual(self.category.state, "draft")  # Ensure we start as draft
        payload = self.payload.copy()
        payload['review'] = 1  # Include the review in the payload
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 403)

    def test_contributor_submit_for_review(self):
        """Ensure contributors CAN submit for review"""
        self.assertEqual(self.category.state, "draft")  # Ensure we start as draft
        payload = self.payload.copy()
        payload['review'] = 1  # Include the review in the payload
        self.client.login(username="contrib", password="pass")
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestCategoryDeleteView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestCategoryDeleteView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestCategoryDeleteView).setUpTestData()
        # Define a user that will be a package contributor.
        User = get_user_model()
        args = ("contrib", "contrib@example.com", "pass")
        cls.contributor = User.objects.create_user(*args)
        cls.contributor.groups.add(get_or_create_content_viewers())

        # Create a Category
        cls.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )
        cls.url = cls.category.get_delete_url()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

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

    def test_contributor_get(self):
        resp = self.client.login(username="contrib", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_anon_post(self):
        resp = self.ua_client.post(self.url)
        self.assertEqual(resp.status_code, 302)

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

    def test_contributor_post(self):
        resp = self.client.login(username="contrib", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
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
        )

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

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


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
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
        )
        cls.url = cls.goal.get_absolute_url()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

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

    def test_viewer_get_changed_url(self):
        """Ensure we can still access a page if the title_slug changes."""
        self.client.login(username="viewer", password="pass")

        # if the object's title changes, the old url should still work.
        self.goal.title = "Some New thing that's different"
        self.goal.save()
        self.assertNotEqual(self.goal.get_absolute_url(), self.url)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestGoalCreateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestGoalCreateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client
        cls.url = reverse("goals:goal-create")

    @classmethod
    def setUpTestData(cls):
        super(cls, TestGoalCreateView).setUpTestData()

        # Define a user that will be a package contributor.
        User = get_user_model()
        args = ("contrib", "contrib@example.com", "pass")
        cls.contributor = User.objects.create_user(*args)
        cls.contributor.groups.add(get_or_create_content_viewers())

        cls.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )
        cls.category.contributors.add(cls.contributor)

        cls.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
        )

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/goal_form.html")

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_contributor_get(self):
        self.client.login(username="contrib", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_admin_post(self):
        """Ensure Admins can create new Goals"""
        self.client.login(username="admin", password="pass")
        payload = {
            'title': 'Created Goal',
            'description': 'whee',
            'categories': self.category.id,
            'sequence_order': 0,
        }
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Goal.objects.filter(title="Created Goal").exists())

        # Ensure we redirect to the detail page afterwards
        obj = Goal.objects.get(title="Created Goal")
        self.assertIn(obj.get_absolute_url(), resp.get('Location', ''))
        Goal.objects.filter(id=obj.id).delete()  # clean up

    def test_contributor_post(self):
        """Ensure Package Contributors can create new Goals"""
        self.client.login(username="contrib", password="pass")
        payload = {
            'title': 'New Goal',
            'description': 'whee',
            'categories': self.category.id,
            'sequence_order': 1,
        }
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Goal.objects.filter(title="New Goal").exists())

        # Ensure we redirect to the detail page afterwards
        obj = Goal.objects.get(title="New Goal")
        self.assertIn(obj.get_absolute_url(), resp.get('Location', ''))
        Goal.objects.filter(id=obj.id).delete()  # clean up


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
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
        )
        cls.url = cls.goal.get_duplicate_url()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/goal_form.html")
        title_copy = "Copy of {0}".format(self.goal.title)
        self.assertContains(resp, title_copy)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
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
        self.assertEqual(resp.status_code, 302)

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
        self.assertEqual(resp.status_code, 302)

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


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestGoalUpdateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestGoalUpdateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestGoalUpdateView).setUpTestData()
        # Define a user that will be a package contributor.
        User = get_user_model()
        args = ("contrib", "contrib@example.com", "pass")
        cls.contributor = User.objects.create_user(*args)
        cls.contributor.groups.add(get_or_create_content_viewers())

        # Create a Category
        cls.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )
        cls.category.contributors.add(cls.contributor)

        cls.payload = {
            'categories': cls.category.id,
            'sequence_order': 1,
            'title': 'A',
            'description': 'B',
            'notes': '',
        }

    def setUp(self):
        # Re-create the goal
        self.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
            created_by=self.author
        )
        self.goal.categories.add(self.category)

        # Note: We can't submit a goal for review unless it has a
        # published/in-review child action.
        self.action = mommy.make(Action, title='A', state='published')
        self.action.goals.add(self.goal)

        self.url = self.goal.get_update_url()

    def tearDown(self):
        Goal.objects.filter(id=self.goal.id).delete()
        Action.objects.filter(id=self.action.id).delete()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

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

    def test_contributor_get(self):
        self.client.login(username="contrib", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_other_contributor_get(self):
        """Ensure a package contributor cannot update a Goal that's not
        in their package."""
        User = get_user_model()
        user = User.objects.create_user("x", "x@x.x", 'xxx')
        user.groups.add(get_or_create_content_viewers())

        # Other category in which user is a contributor
        cat = Category.objects.create(order=2, title="other cat")
        cat.contributors.add(user)

        # This contributor should not be able to update this Category
        self.client.login(username="x", password="xxx")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

        cat.delete()
        user.delete()

    def test_anon_post(self):
        resp = self.ua_client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)

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
        """If you change the title of an existing object to something that
        would be a duplicate, ... this is OK now."""
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
            'sequence_order': 0,
            'categories': self.category.id,
        })

        # We should get redirected
        self.assertEqual(resp.status_code, 302)

        # Clean up.
        goal.delete()

    def test_contributor_post(self):
        """Ensure Contributors can POST updates."""
        self.client.login(username="contrib", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Goal.objects.get(pk=self.goal.id).title, 'A')

    def test_other_contributor_post(self):
        """Ensure a package contributor cannot update a Goal that's not
        in their package."""
        User = get_user_model()
        user = User.objects.create_user("x", "x@x.x", 'xxx')
        content_viewer_group = get_or_create_content_viewers()
        user.groups.add(content_viewer_group)

        # Other category in which user is a contributor
        cat = Category.objects.create(order=2, title="other cat")
        cat.contributors.add(user)

        self.client.login(username="x", password="xxx")
        payload = self.payload.copy()
        payload['title'] = 'contrib edit'
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 403)

        cat.delete()
        user.delete()

    def test_author_post(self):
        """Ensure Authors can POST updates."""
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
        """Ensure VIEWers cannot post updates."""
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)

    def test_viewer_submit_for_review(self):
        """Ensure viewers cannot submit for review."""
        self.assertEqual(self.goal.state, "draft")  # Ensure we start as draft
        payload = self.payload.copy()
        payload['review'] = 1  # Include the review in the payload
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 403)

    def test_editor_submit_for_review(self):
        """Ensure editors can submit for review."""
        self.assertEqual(self.goal.state, "draft")  # Ensure we start as draft
        payload = self.payload.copy()
        payload['review'] = 1  # Include the review in the payload
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)

        updated_goal = Goal.objects.get(pk=self.goal.pk)
        self.assertEqual(updated_goal.state, "pending-review")

    def test_admin_submit_for_review(self):
        """Ensure admins can submit for review."""
        self.assertEqual(self.goal.state, "draft")  # Ensure we start as draft
        payload = self.payload.copy()
        payload['review'] = 1  # Include the review in the payload
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)

        updated_goal = Goal.objects.get(pk=self.goal.pk)
        self.assertEqual(updated_goal.state, "pending-review")

    def test_author_submit_for_review(self):
        """Ensure authors can submit for review."""
        self.assertEqual(self.goal.state, "draft")  # Ensure we start as draft
        payload = self.payload.copy()
        payload['review'] = 1  # Include the review in the payload
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)

        updated_goal = Goal.objects.get(pk=self.goal.pk)
        self.assertEqual(updated_goal.state, "pending-review")

    def test_redirect_after_save(self):
        """Ensure we redirect to the detail page after saving"""
        payload = self.payload.copy()
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)

        goal = Goal.objects.get(pk=self.goal.id)
        self.assertIn(goal.get_absolute_url(), resp.get("Location", ''))


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestGoalDeleteView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestGoalDeleteView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    def setUp(self):
        # Define a user that will be a package contributor.
        User = get_user_model()
        args = ("contrib", "contrib@example.com", "pass")
        self.contributor = User.objects.create_user(*args)
        self.contributor.groups.add(get_or_create_content_viewers())

        # Create a Category
        self.category = Category.objects.create(order=1, title='Cat')
        self.category.contributors.add(self.contributor)

        # Create a Goal
        self.goal = Goal.objects.create(
            title="Title for Test Goal",
            description="A Description",
        )
        self.goal.categories.add(self.category)
        self.url = self.goal.get_delete_url()

    def tearDown(self):
        Goal.objects.filter(id=self.goal.id).delete()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

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

    def test_contributor_get(self):
        self.client.login(username="contrib", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_anon_post(self):
        resp = self.ua_client.post(self.url)
        self.assertEqual(resp.status_code, 302)

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

    def test_contributor_post(self):
        self.client.login(username="contrib", password="pass")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestActionListView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestActionListView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client
        cls.url = reverse("goals:action-list")

    @classmethod
    def setUpTestData(cls):
        super(cls, TestActionListView).setUpTestData()
        cls.action = Action.objects.create(title="Test Action")

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

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


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestActionDetailView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestActionDetailView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestActionDetailView).setUpTestData()
        cls.action = Action.objects.create(title="Test Action")
        cls.url = cls.action.get_absolute_url()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

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

    def test_viewer_get_changed_url(self):
        """Ensure we can still access a page if the title_slug changes."""
        self.client.login(username="viewer", password="pass")

        # if the action's title changes, the old url should still work.
        self.action.title = "Some New thing that's different"
        self.action.save()
        self.assertNotEqual(self.action.get_absolute_url(), self.url)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestActionCreateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestActionCreateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client
        cls.url = reverse("goals:action-create")

    @classmethod
    def setUpTestData(cls):
        super(cls, TestActionCreateView).setUpTestData()
        cls.cat = mommy.make(Category, title="C", order=0, state='published')
        cls.goal = mommy.make(Goal, title="Goal", state='published')
        cls.goal.categories.add(cls.cat)

        cls.payload = {
            'sequence_order': 1,
            'title': 'New',
            'goals': [cls.goal.id],
            'action_type': Action.SHOWING,
            'trigger-time': '22:00',
            'trigger-trigger_date': '08/20/2015',
            'trigger-recurrences': 'RRULE:FREQ=WEEKLY;BYDAY=SA',
            'trigger-stop_on_complete': '',
            'trigger-relative_value': '0',
            'trigger-relative_units': '',
            'priority': Action.LOW,
        }

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/action_form.html")
        self.assertIn("actions", resp.context)

    def test_admin_get_with_actiontype_params(self):
        self.client.login(username="admin", password="pass")
        url = '{}?actiontype={}'.format(self.url, Action.SHOWING)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("form", resp.context)
        self.assertEqual(
            resp.context['form'].initial['action_type'],
            Action.SHOWING
        )

    def test_admin_get_with_date_get_params(self):
        self.client.login(username="admin", password="pass")
        url = '{}?date={}'.format(self.url, "2015-12-25")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("trigger_form", resp.context)
        self.assertEqual(
            resp.context['trigger_form'].initial['trigger_date'],
            "12/25/2015"
        )

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
        self.assertEqual(resp.status_code, 302)

    def test_admin_post_empty_form(self):
        """This is an edge case, but it shouldn't cause a 500"""
        data = {
            'sequence_order': 0,
            'title': '',
            'action_type': '',
            'trigger-time': '',
            'trigger-trigger_date': '',
            'trigger-recurrences': '',
            'trigger-stop_on_complete': '',
            'trigger-relative_value': '0',
            'trigger-relative_units': '',
        }
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)

    def test_admin_post(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Action.objects.filter(title="New").exists())

        # Ensure we redirect to the detail page afterwards
        obj = Action.objects.get(title="New")
        self.assertIn(obj.get_absolute_url(), resp.get('Location', ''))
        Action.objects.filter(title="New").delete()  # clean up

    def test_admin_post_and_review(self):
        self.client.login(username="admin", password="pass")
        payload = self.payload
        payload.update({"review": 1})
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)
        qs = Action.objects.filter(title="New", state='pending-review')
        self.assertTrue(qs.exists())

    def test_admin_post_with_long_values(self):
        """Verify we can create objects that hit text-length limits"""
        # 256 title / notification_text
        payload = {
            'sequence_order': 0,
            'title': 'X' * 256,
            'goals': [self.goal.id],
            'notification_text': 'Y' * 256,
            'action_type': 'showing',
            'priority': '3',
            'more_info': '',
            'source_link': '',
            'external_resource': '',
            'external_resource_name': '',
            'source_notes': '',
            'icon': '',
            'description': '',
            'trigger-time_of_day': '',
            'trigger-frequency': '',
            'trigger-time': '',
            'trigger-trigger_date': '',
            'trigger-recurrences': '',
            'trigger-start_when_selected': '',
            'trigger-stop_on_complete': '',
            'trigger-relative_value': '0',
            'trigger-relative_units': '',
        }
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)

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


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestActionDuplicateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestActionDuplicateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestActionDuplicateView).setUpTestData()
        cls.action = Action.objects.create(title="Test Action")
        cls.url = cls.action.get_duplicate_url()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/action_form.html")
        title_copy = "Copy of {0}".format(self.action.title)
        self.assertContains(resp, title_copy)
        self.assertIn("actions", resp.context)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestActionPublishView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestActionPublishView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestActionPublishView).setUpTestData()

        cls.cat = mommy.make(Category, title="C", order=0, state='published')
        cls.goal = mommy.make(Goal, title="Goal", state='published')
        cls.goal.categories.add(cls.cat)

        cls.action = Action.objects.create(title="Test Action")
        cls.action.goals.add(cls.goal)

        cls.url = cls.action.get_publish_url()

    def setUp(self):
        self.action.review()
        self.action.save()

    def tearDown(self):
        self.action.draft()
        self.action.save()

    def test_anon_publish(self):
        resp = self.ua_client.post(self.url, {"publish": "1"})
        self.assertEqual(resp.status_code, 302)

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
        self.assertEqual(resp.status_code, 302)

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


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestActionUpdateView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestActionUpdateView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super(cls, TestActionUpdateView).setUpTestData()
        # Define a user that will be a package contributor.
        User = get_user_model()
        args = ("contrib", "contrib@example.com", "pass")
        cls.contributor = User.objects.create_user(*args)
        cls.contributor.groups.add(get_or_create_content_viewers())

        # Create a Category
        cls.category = Category.objects.create(
            order=1,
            title='Test Category',
            description='Some explanation!',
        )
        cls.category.contributors.add(cls.contributor)
        cls.goal = Goal.objects.create(title="Goal")
        cls.goal.categories.add(cls.category)

        cls.payload = {
            'sequence_order': 1,
            'title': 'U',
            'action_type': Action.SHOWING,
            'goals': [cls.goal.id],
            'trigger-time': '22:00',
            'trigger-trigger_date': '08/20/2015',
            'trigger-recurrences': 'RRULE:FREQ=WEEKLY;BYDAY=SA',
            'trigger-stop_on_complete': False,
            'trigger-relative_value': '0',
            'trigger-relative_units': '',
            'priority': Action.LOW,
        }

    def setUp(self):
        # Re-create the Action
        self.action = Action.objects.create(
            title="Test Action",
            sequence_order=1,
            created_by=self.author
        )
        self.action.goals.add(self.goal)
        self.url = self.action.get_update_url()

    def tearDown(self):
        Action.objects.filter(id=self.action.id).delete()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/action_form.html")
        self.assertContains(resp, self.action.title)

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
            title="Other",
            sequence_order=2,
            created_by=self.editor
        )
        self.client.login(username="author", password="pass")
        resp = self.client.get(a.get_update_url())
        self.assertEqual(resp.status_code, 403)
        a.delete()  # Clean up

    def test_contributor_get(self):
        self.client.login(username="contrib", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_other_contributor_get(self):
        """When a package contributor tries to update an Action that's not
        in their package."""
        User = get_user_model()
        user = User.objects.create_user("x", "x@x.x", 'xxx')
        content_viewer_group = get_or_create_content_viewers()
        user.groups.add(content_viewer_group)

        # Other category in which user is a contributor
        cat = Category.objects.create(order=2, title="other cat")
        cat.contributors.add(user)

        # This contributor should not be able to update this Category
        self.client.login(username="x", password="xxx")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

        cat.delete()
        user.delete()

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_anon_post(self):
        resp = self.ua_client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)

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

    def test_contributor_post(self):
        self.client.login(username="contrib", password="pass")
        payload = self.payload.copy()
        payload['title'] = 'contrib edit'
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Action.objects.get(pk=self.action.pk).title,
            "contrib edit"
        )

    def test_other_contributor_post(self):
        """Ensure a package contributor cannot update an Action that's not
        in their package."""
        User = get_user_model()
        user = User.objects.create_user("x", "x@x.x", 'xxx')
        content_viewer_group = get_or_create_content_viewers()
        user.groups.add(content_viewer_group)

        # Other category in which user is a contributor
        cat = Category.objects.create(order=2, title="other cat")
        cat.contributors.add(user)

        self.client.login(username="x", password="xxx")
        payload = self.payload.copy()
        payload['title'] = 'contrib edit'
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 403)

        cat.delete()
        user.delete()

    def test_author_post(self):
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Action.objects.get(pk=self.action.pk).title, "U")

    def test_author_post_other_object(self):
        """Ensure authors cannot update someone else's content."""
        a = Action.objects.create(
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

    def test_viewer_submit_for_review(self):
        """Ensure viewers cannot submit for review."""
        self.assertEqual(self.action.state, "draft")  # Ensure we start as draft
        payload = self.payload.copy()
        payload['review'] = 1  # Include the review in the payload
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 403)

    def test_editor_submit_for_review(self):
        """Ensure editors can submit for review."""
        self.assertEqual(self.action.state, "draft")  # Ensure we start as draft
        payload = self.payload.copy()
        payload['review'] = 1  # Include the review in the payload
        self.client.login(username="editor", password="pass")
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Action.objects.get(pk=self.action.pk).state, "pending-review")

    def test_admin_submit_for_review(self):
        """Ensure admins can submit for review."""
        self.assertEqual(self.action.state, "draft")  # Ensure we start as draft
        payload = self.payload.copy()
        payload['review'] = 1  # Include the review in the payload
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Action.objects.get(pk=self.action.pk).state, "pending-review")

    def test_author_submit_for_review(self):
        """Ensure authors can submit for review."""
        self.assertEqual(self.action.state, "draft")  # Ensure we start as draft
        payload = self.payload.copy()
        payload['review'] = 1  # Include the review in the payload
        self.client.login(username="author", password="pass")
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Action.objects.get(pk=self.action.pk).state, "pending-review")

    def test_redirect_after_save(self):
        """Ensure we redirect to the detail page after saving"""
        self.client.login(username="admin", password="pass")
        resp = self.client.post(self.url, self.payload.copy())
        self.assertEqual(resp.status_code, 302)

        action = Action.objects.get(pk=self.action.id)
        self.assertIn(action.get_absolute_url(), resp.get("Location", ''))


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestActionDeleteView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super(cls, TestActionDeleteView).setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    def setUp(self):
        # Create an Action
        self.action = Action.objects.create(title="Test Action")
        self.url = self.action.get_delete_url()

    def tearDown(self):
        Action.objects.filter(id=self.action.id).delete()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

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
        self.assertEqual(resp.status_code, 302)

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


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestPackageEnrollmentDeleteView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        User = get_user_model()
        User.objects.all().delete()
        for model in [Category, Goal, Action]:
            model.objects.all().delete()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        User = get_user_model()

        # Create a contributor for the class.
        content_author_group = get_or_create_content_authors()
        args = ("contributor", "contributor@example.com", "pass")
        cls.contributor = User.objects.create_user(*args)
        cls.contributor.groups.add(content_author_group)

        # Create permissions for the contirbutor
        for perm in ContentPermissions.package_managers:
            perm = Permission.objects.get(codename=perm.split(".")[1])
            cls.contributor.user_permissions.add(perm)

        # Create the Category and the content hierarchy
        cls.category = Category.objects.create(
            packaged_content=True,
            order=25,
            title="Test Package Category",
            state="published",
            created_by=cls.editor,
        )
        cls.category.contributors.add(cls.contributor)
        cls.category.save()
        cls.goal_a = Goal.objects.create(title="Pkg Goal A", state="published")
        cls.goal_a.categories.add(cls.category)
        cls.action_a = Action.objects.create(title="Pkg Action A", state="published")
        cls.action_a.goals.add(cls.goal_a)

        # Set up an enrolled user
        args = ('user', 'user@example.com', 'pass')
        user = User.objects.create_user(*args)
        cls.package = PackageEnrollment.objects.create(
            user=user,
            category=cls.category,
            enrolled_by=cls.contributor
        )
        cls.package.goals.add(cls.goal_a)
        cls.package.accept()

        cls.url = reverse('goals:package-enrollment-delete', args=[cls.package.id])

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_contributor_get(self):
        self.client.login(username="contributor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/packageenrollment_confirm_delete.html")

    def test_contributor_post(self):
        self.client.login(username="contributor", password="pass")
        resp = self.client.post(self.url, {})  # NOTE: no payload
        self.assertEqual(resp.status_code, 302)

        package = PackageEnrollment.objects.filter(pk=self.package.pk)
        self.assertFalse(package.exists())


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestPackageEnrollmentView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        User = get_user_model()
        User.objects.all().delete()
        for model in [Category, Goal, Action]:
            model.objects.all().delete()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        User = get_user_model()

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
        cls.category.contributors.add(cls.contributor)
        cls.category.save()

        cls.goal_a = Goal.objects.create(title="Pkg Goal A", state="published")
        cls.goal_b = Goal.objects.create(title="Pkg Goal B", state="published")
        cls.goal_a.categories.add(cls.category)
        cls.goal_b.categories.add(cls.category)

        cls.action_a = Action.objects.create(title="Pkg Action A", state="published")
        cls.action_a.goals.add(cls.goal_a)
        cls.action_b = Action.objects.create(title="Pkg Action B", state="published")
        cls.action_b.goals.add(cls.goal_b)

        # URL and POST payload
        cls.payload = {
            'email_addresses': 'new-user@example.com',
            'packaged_goals': [cls.goal_a.id],
        }
        cls.url = cls.category.get_enroll_url()
        cls.success_url = cls.category.get_view_enrollment_url()

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

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
        self.assertEqual(resp.status_code, 302)

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


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestAcceptEnrollmentCompleteView(TestCase):
    """Simple, publicly-available template."""

    def test_get(self):
        resp = self.client.get(reverse("goals:accept-enrollment-complete"))
        self.assertEqual(resp.status_code, 200)
        self.client.logout()


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestEnrollmentReminderView(TestCaseWithGroups):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        User = get_user_model()
        User.objects.all().delete()
        for model in [Category, Goal, Action]:
            model.objects.all().delete()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        User = get_user_model()

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
        cls.category.contributors.add(cls.contributor)
        cls.category.save()

        # An Un-accepted Enrollment
        args = ("unenrolled", "unerolled@example.com", "pass")
        cls.user = User.objects.create_user(*args)
        cls.enrollment = PackageEnrollment.objects.create(
            user=cls.user,
            category=cls.category,
            accepted=False,
            enrolled_by=cls.contributor,
        )

        # URL and POST payload
        cls.payload = {'message': 'Email Content'}
        cls.url = reverse("goals:package-reminder", args=[cls.category.id])
        cls.success_url = cls.category.get_view_enrollment_url()
        cls.enrollments = PackageEnrollment.objects.filter(accepted=False)

    def test_anon_get(self):
        resp = self.ua_client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_admin_get(self):
        self.client.login(username="admin", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/package_enrollment_reminder.html")
        self.assertIn("enrollments", resp.context)
        self.assertIn("category", resp.context)
        self.assertIn("form", resp.context)

    def test_contributor_get(self):
        self.client.login(username="contributor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/package_enrollment_reminder.html")
        self.assertIn("enrollments", resp.context)
        self.assertIn("category", resp.context)
        self.assertIn("form", resp.context)

    def test_editor_get(self):
        self.client.login(username="editor", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/package_enrollment_reminder.html")
        self.assertIn("enrollments", resp.context)
        self.assertIn("category", resp.context)
        self.assertIn("form", resp.context)

    def test_author_get(self):
        self.client.login(username="author", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/package_enrollment_reminder.html")
        self.assertIn("enrollments", resp.context)
        self.assertIn("category", resp.context)
        self.assertIn("form", resp.context)

    def test_viewer_get(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_anon_post(self):
        resp = self.ua_client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)

    def test_admin_post(self):
        self.client.login(username="admin", password="pass")
        with patch('goals.views.send_package_enrollment_batch'):
            resp = self.client.post(self.url, self.payload)
            self.assertEqual(resp.status_code, 302)
            self.assertRedirects(resp, self.success_url)

    def test_editor_post(self):
        self.client.login(username="editor", password="pass")
        with patch('goals.views.send_package_enrollment_batch'):
            resp = self.client.post(self.url, self.payload)
            self.assertEqual(resp.status_code, 302)
            self.assertRedirects(resp, self.success_url)

    def test_author_post(self):
        self.client.login(username="author", password="pass")
        with patch('goals.views.send_package_enrollment_batch'):
            resp = self.client.post(self.url, self.payload)
            self.assertEqual(resp.status_code, 302)
            self.assertRedirects(resp, self.success_url)

    def test_viewer_post(self):
        self.client.login(username="viewer", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 403)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestProgramListView(TestCaseWithGroups):
    # NOTE: tests are named with this convention:
    # test_[auth-group]_[http-verb]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client
        cls.url = reverse("goals:program-list")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Staff user
        User = get_user_model()
        user = User.objects.create_user("x", "x@x.x", "xxx")
        user.is_staff = True
        user.save()

        # Create an Org
        cls.org = Organization.objects.create(name="Org")
        cls.program = Program.objects.create(name="Program", organization=cls.org)

    def test_unauthed_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_staff_get(self):
        self.client.login(username="x", password="xxx")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/program_list.html")
        self.assertIn('programs', resp.context)
        self.assertContains(resp, self.program.name)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestProgramDetailView(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Staff user
        User = get_user_model()
        user = User.objects.create_user("x", "x@x.x", "xxx")
        user.is_staff = True
        user.save()

        # Create an Org
        cls.org = Organization.objects.create(name="Org")
        cls.program = Program.objects.create(name="Program", organization=cls.org)
        cls.url = cls.program.get_absolute_url()

    def test_unauthed_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_staff_get(self):
        self.client.login(username="x", password="xxx")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/program_detail.html")
        self.assertIn("program", resp.context)
        self.assertIn("organization", resp.context)


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestProgramCreateView(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Staff user
        User = get_user_model()
        user = User.objects.create_user("x", "x@x.x", "xxx")
        user.is_staff = True
        user.save()

        # Create Content + an Org
        cls.org = Organization.objects.create(name="Org")
        cls.category = Category.objects.create(
            order=1,
            title="Cat",
            state="published"
        )
        cls.category.organizations.add(cls.org)
        cls.goal = Goal.objects.create(title="Goal", state="published")
        cls.goal.categories.add(cls.category)
        cls.goal.save()

        cls.url = reverse('goals:program-create',
                          args=[cls.org.id, cls.org.name_slug])

        # Program Payload
        cls.payload = {
            'name': 'New Program',
            'organization': cls.org.id,
            'categories': [cls.category.id],
            'auto_enrolled_goals': [cls.goal.id],
        }

    def test_unauthed_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_unauthed_post(self):
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)

    def test_staff_get(self):
        self.client.login(username="x", password="xxx")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/program_form.html")
        self.assertIn("organization", resp.context)

    def test_staff_post(self):
        # Test pre-condition
        self.assertFalse(Program.objects.filter(name="New Program").exists())

        self.client.login(username="x", password="xxx")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)

        # Test post-condition
        self.assertTrue(Program.objects.filter(name="New Program").exists())


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestProgramUpdateView(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Staff user
        User = get_user_model()
        user = User.objects.create_user("x", "x@x.x", "xxx")
        user.is_staff = True
        user.save()

        # Create Content + an Org
        cls.org = Organization.objects.create(name="Org")
        cls.category = Category.objects.create(
            order=1,
            title="Cat",
            state="published"
        )
        cls.category.organizations.add(cls.org)

        # Goal 1 is already part of the program.
        cls.goal1 = Goal.objects.create(title="G1", state="published")
        cls.goal1.categories.add(cls.category)
        cls.goal1.save()

        # Goal 2 (and it's content) will be added to the program later.
        cls.goal2 = Goal.objects.create(title="G2", state="published")
        cls.goal2.categories.add(cls.category)
        cls.goal2.save()

        cls.action = Action.objects.create(title="A", state="published")
        cls.action.goals.add(cls.goal1)

        cls.program = Program.objects.create(name="PRG", organization=cls.org)
        cls.program.categories.add(cls.category)
        cls.program.auto_enrolled_goals.add(cls.goal1)

        cls.url = cls.program.get_update_url()

    def test_unauthed_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_unauthed_post(self):
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, 302)

    def test_staff_get(self):
        self.client.login(username="x", password="xxx")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/program_form.html")
        self.assertIn("organization", resp.context)

    def test_staff_post(self):
        program = Program.objects.create(name="Test", organization=self.org)
        program.categories.add(self.category)
        program.auto_enrolled_goals.add(self.goal1)

        payload = {
            'name': 'Updated',
            'categories': [self.category.id],
            'auto_enrolled_goals': [self.goal1.id],
        }

        self.client.login(username="x", password="xxx")
        resp = self.client.post(program.get_update_url(), payload)
        self.assertEqual(resp.status_code, 302)

        # Verify Result
        program = Program.objects.get(pk=program.id)
        self.assertEqual(program.name, "Updated")

    def test_staff_post_new_goals_enrolls_students(self):
        """Adding a published goal to a program should enroll it's members."""
        User = get_user_model()
        user = User.objects.create(username="member", email="m@b.r")
        self.org.members.add(user)
        self.program.members.add(user)

        # pre conditions (Goal 1 has no actions)
        self.assertFalse(user.useraction_set.exists())

        payload = {
            'name': 'PRG (updated)',
            'categories': [self.category.id],
            'auto_enrolled_goals': [self.goal1.id, self.goal2.id],  # adding Goal2
        }

        self.client.login(username="x", password="xxx")
        resp = self.client.post(self.url, payload)
        self.assertEqual(resp.status_code, 302)

        get_worker().work(burst=True)  # Processes all jobs then stop.

        # Verify Result (user has Goal2 and Action)
        program = Program.objects.get(pk=self.program.id)
        self.assertEqual(program.name, "PRG (updated)")

        self.assertTrue(user.useraction_set.exists())
        self.assertTrue(user.usergoal_set.filter(goal__title="G2").exists())
        self.assertTrue(user.useraction_set.filter(action__title="A").exists())


@override_settings(SESSION_ENGINE=TEST_SESSION_ENGINE)
@override_settings(RQ_QUEUES=TEST_RQ_QUEUES)
@override_settings(CACHES=TEST_CACHES)
class TestProgramDeleteView(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ua_client = Client()  # Create an Unauthenticated client

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Staff user
        User = get_user_model()
        cls.user = User.objects.create_user("x", "x@x.x", "xxx")
        cls.user.is_staff = True
        cls.user.save()

        cls.org = Organization.objects.create(name="Org")
        cls.program = Program.objects.create(name="Program", organization=cls.org)
        cls.url = cls.program.get_delete_url()

    def test_unauthed_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_unauthed_post(self):
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, 302)

    def test_staff_get(self):
        self.client.login(username="x", password="xxx")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/program_confirm_delete.html")
        self.assertIn("organization", resp.context)
        self.client.logout()

    def test_staff_get_when_members(self):
        """You cannot delete a program with members."""

        # Create a program with members
        program = Program.objects.create(name="P", organization=self.org)
        program.members.add(self.user)
        program.save()

        self.client.login(username="x", password="xxx")
        resp = self.client.get(program.get_delete_url())
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "goals/program_confirm_delete.html")
        self.assertIn("organization", resp.context)
        self.assertContains(resp, "Deletion is not currently supported.")
        self.client.logout()

        program.delete()

    def test_staff_post(self):
        self.client.login(username="x", password="xxx")
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, 302)

        # Test post-condition
        self.assertFalse(Program.objects.filter(name="Program").exists())
        self.client.logout()

    def test_staff_post_when_members(self):
        """You cannot delete a program with members."""

        # Create a program with members
        program = Program.objects.create(name="P", organization=self.org)
        program.members.add(self.user)
        program.save()

        self.client.login(username="x", password="xxx")
        resp = self.client.post(program.get_delete_url(), {})
        self.assertEqual(resp.status_code, 403)
        self.client.logout()

        # Verify program still exists
        self.assertTrue(Program.objects.filter(id=program.id).exists())
        program.delete()
