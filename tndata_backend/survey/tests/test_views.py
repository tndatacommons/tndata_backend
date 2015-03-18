from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import Client, TestCase

from .. models import (
    LikertQuestion,
    MultipleChoiceQuestion,
    OpenEndedQuestion,
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
        url = reverse("survey:index")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestLikertQuestionListView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a question
        self.question = LikertQuestion.objects.create(
            order=1,
            text='Test Question',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        LikertQuestion.objects.filter(id=self.question.id).delete()

    def test_get(self):
        url = reverse("survey:likert-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "survey/likertquestion_list.html")
        self.assertIn("questions", resp.context)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestLikertQuestionDetailView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a LikertQuestion
        self.question = LikertQuestion.objects.create(
            order=1,
            text='Test LikertQuestion',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        LikertQuestion.objects.filter(id=self.question.id).delete()

    def test_get(self):
        url = self.question.get_absolute_url()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "survey/likertquestion_detail.html")
        self.assertContains(resp, self.question.text)
        self.assertIn("question", resp.context)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestLikertQuestionCreateView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a LikertQuestion
        self.question = LikertQuestion.objects.create(
            order=1,
            text='Test LikertQuestion',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        LikertQuestion.objects.filter(id=self.question.id).delete()

    def test_get(self):
        url = reverse("survey:likert-create")

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "survey/likertquestion_form.html")
        self.assertContains(resp, self.question.text)
        self.assertIn("questions", resp.context)


class TestLikertQuestionUpdateView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a LikertQuestion
        self.question = LikertQuestion.objects.create(
            order=1,
            text='Test LikertQuestion',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        LikertQuestion.objects.filter(id=self.question.id).delete()

    def test_get(self):
        url = self.question.get_update_url()

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "survey/likertquestion_form.html")
        self.assertContains(resp, self.question.text)
        self.assertIn("questions", resp.context)


class TestLikertQuestionDeleteView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a LikertQuestion
        self.question = LikertQuestion.objects.create(
            order=1,
            text='Test LikertQuestion',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        LikertQuestion.objects.filter(id=self.question.id).delete()

    def test_get(self):
        url = self.question.get_delete_url()
        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "survey/likertquestion_confirm_delete.html")
        self.assertIn("question", resp.context)

    def test_post(self):
        url = self.question.get_delete_url()
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse("survey:index"))


class TestMultipleChoiceQuestionListView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a question
        self.question = MultipleChoiceQuestion.objects.create(
            order=1,
            text='Test Question',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        MultipleChoiceQuestion.objects.filter(id=self.question.id).delete()

    def test_get(self):
        url = reverse("survey:multiplechoice-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "survey/multiplechoicequestion_list.html")
        self.assertIn("questions", resp.context)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestMultipleChoiceQuestionDetailView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a MultipleChoiceQuestion
        self.question = MultipleChoiceQuestion.objects.create(
            order=1,
            text='Test MultipleChoiceQuestion',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        MultipleChoiceQuestion.objects.filter(id=self.question.id).delete()

    def test_get(self):
        url = self.question.get_absolute_url()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "survey/multiplechoicequestion_detail.html")
        self.assertContains(resp, self.question.text)
        self.assertIn("question", resp.context)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestMultipleChoiceQuestionCreateView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a MultipleChoiceQuestion
        self.question = MultipleChoiceQuestion.objects.create(
            order=1,
            text='Test MultipleChoiceQuestion',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        MultipleChoiceQuestion.objects.filter(id=self.question.id).delete()

    def test_get(self):
        url = reverse("survey:multiplechoice-create")

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "survey/multiplechoicequestion_form.html")
        self.assertContains(resp, self.question.text)
        self.assertIn("questions", resp.context)


class TestMultipleChoiceQuestionUpdateView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a MultipleChoiceQuestion
        self.question = MultipleChoiceQuestion.objects.create(
            order=1,
            text='Test MultipleChoiceQuestion',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        MultipleChoiceQuestion.objects.filter(id=self.question.id).delete()

    def test_get(self):
        url = self.question.get_update_url()

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "survey/multiplechoicequestion_form.html")
        self.assertContains(resp, self.question.text)
        self.assertIn("questions", resp.context)


class TestMultipleChoiceQuestionDeleteView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a MultipleChoiceQuestion
        self.question = MultipleChoiceQuestion.objects.create(
            order=1,
            text='Test MultipleChoiceQuestion',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        MultipleChoiceQuestion.objects.filter(id=self.question.id).delete()

    def test_get(self):
        url = self.question.get_delete_url()
        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "survey/multiplechoicequestion_confirm_delete.html")
        self.assertIn("question", resp.context)

    def test_post(self):
        url = self.question.get_delete_url()
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse("survey:index"))


class TestOpenEndedQuestionListView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a question
        self.question = OpenEndedQuestion.objects.create(
            order=1,
            text='Test Question',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        OpenEndedQuestion.objects.filter(id=self.question.id).delete()

    def test_get(self):
        url = reverse("survey:openended-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "survey/openendedquestion_list.html")
        self.assertIn("questions", resp.context)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestOpenEndedQuestionDetailView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a OpenEndedQuestion
        self.question = OpenEndedQuestion.objects.create(
            order=1,
            text='Test OpenEndedQuestion',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        OpenEndedQuestion.objects.filter(id=self.question.id).delete()

    def test_get(self):
        url = self.question.get_absolute_url()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "survey/openendedquestion_detail.html")
        self.assertContains(resp, self.question.text)
        self.assertIn("question", resp.context)

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)


class TestOpenEndedQuestionCreateView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a OpenEndedQuestion
        self.question = OpenEndedQuestion.objects.create(
            order=1,
            text='Test OpenEndedQuestion',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        OpenEndedQuestion.objects.filter(id=self.question.id).delete()

    def test_get(self):
        url = reverse("survey:openended-create")

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "survey/openendedquestion_form.html")
        self.assertContains(resp, self.question.text)
        self.assertIn("questions", resp.context)


class TestOpenEndedQuestionUpdateView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a OpenEndedQuestion
        self.question = OpenEndedQuestion.objects.create(
            order=1,
            text='Test OpenEndedQuestion',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        OpenEndedQuestion.objects.filter(id=self.question.id).delete()

    def test_get(self):
        url = self.question.get_update_url()

        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "survey/openendedquestion_form.html")
        self.assertContains(resp, self.question.text)
        self.assertIn("questions", resp.context)


class TestOpenEndedQuestionDeleteView(TestCase):

    def setUp(self):
        User = get_user_model()
        user_args = ("admin", "admin@example.com", "pass")
        self.user = User.objects.create_superuser(*user_args)

        # Create an Authed/Unauthed client
        self.ua_client = Client()
        self.client.login(username="admin", password="pass")

        # Create a OpenEndedQuestion
        self.question = OpenEndedQuestion.objects.create(
            order=1,
            text='Test OpenEndedQuestion',
        )

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username="admin").delete()
        OpenEndedQuestion.objects.filter(id=self.question.id).delete()

    def test_get(self):
        url = self.question.get_delete_url()
        resp = self.ua_client.get(url)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "survey/openendedquestion_confirm_delete.html")
        self.assertIn("question", resp.context)

    def test_post(self):
        url = self.question.get_delete_url()
        resp = self.client.post(url)
        self.assertRedirects(resp, reverse("survey:index"))
