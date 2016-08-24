from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase

from model_mommy import mommy

# Needed fro the TestProgramEnrollment test suite.
from goals.models import Organization, Program


class TestPasswordResetRequestView(TestCase):

    @classmethod
    def setUpTestData(cls):
        super(cls, TestPasswordResetRequestView).setUpTestData()
        User = get_user_model()
        cls.user = User.objects.create_user("u", "u@example.com", "pass")
        cls.payload = {'email_address': 'u@example.com'}
        cls.url = reverse("utils:password_reset")

    def test_get_unauthed(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_get_authed(self):
        self.client.login(username="u", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.client.logout()

    def test_post_unauthed(self):
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)

    def test_post_authed(self):
        self.client.login(username="u", password="pass")
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 302)
        self.client.logout()

    def test_post_nonexisting_email(self):
        resp = self.client.post(self.url, {'email_address': 'lajsdflkdjf@a.b'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('invalid_email', resp.context.keys())


class TestPasswordResetNotificationView(TestCase):

    @classmethod
    def setUpClass(cls):
        super(cls, TestPasswordResetNotificationView).setUpClass()
        cls.url = reverse("utils:password_reset_notification")

    def test_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)


class TestSetNewPasswordView(TestCase):

    @classmethod
    def setUpTestData(cls):
        super(cls, TestSetNewPasswordView).setUpTestData()
        User = get_user_model()
        cls.user = User.objects.create_user("u", "u@example.com", "pass")
        cls.payload = {'password': 'foo', 'password_confirmation': 'foo'}
        cls.url = reverse("utils:password_reset")

    def test_get_unauthed(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_get_authed(self):
        self.client.login(username="u", password="pass")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.client.logout()


class TestResetPasswordAPI(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        User = get_user_model()
        cls.user = User.objects.create_user("u", "u@example.com", "pass")
        cls.payload = {'email': 'u@example.com'}
        cls.url = reverse("reset-password")

    def test_get(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 405)

    def test_post(self):
        resp = self.client.post(self.url, self.payload)
        self.assertEqual(resp.status_code, 200)

    def test_post_invalid(self):
        resp = self.client.post(self.url, {'email': ''})
        self.assertEqual(resp.status_code, 400)


class TestProgramEnrollment(TestCase):
    """This test suite covers several scenarios for user signup/login that
    involves getting enrolled in an Organzation's Program.

    -----

    Argh :(

    Programs & Organizations are part of the `goals` app, but the signup/login
    workflow is in the `utils` app. So, the tests are here.

    """
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        User = get_user_model()
        cls.user = User.objects.create_user("u", "u@example.com", "secret123")

        cls.organization = mommy.make(Organization, name="Org")
        cls.program = mommy.make(Program, name="Prog", organization=cls.organization)

        cls.join_url = cls.program.get_join_url()
        cls.confirm_url = reverse('utils:confirm')

    def test_get_signup_new_enduser(self):
        """GET requests to join a program should return 200 for an
        un-authenticated user, and render the correct template."""
        resp = self.client.get(self.join_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "utils/signup_enduser.html")

        # Check for some context
        self.assertContains(resp, self.organization)
        self.assertContains(resp, self.program)
        self.assertIn('passthru_vars', resp.context)
        passthru_vars = {
            'organization': str(self.organization.id),
            'program': str(self.program.id)
        }
        self.assertDictEqual(resp.context['passthru_vars'], passthru_vars)
        self.assertIn('ios_url', resp.context)
        self.assertIn('android_url', resp.context)
        self.assertIn('login_url', resp.context)
        self.assertIn('form', resp.context)
        self.assertIn('password_form', resp.context)

    def test_post_signup_new_enduser(self):
        """POSTing data for a new user account should create the account
        and call the `utils.views._setup_enduser` function."""
        User = get_user_model()

        payload = {
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'pw-password': 'secret123',
            'pw-password_confirmation': 'secret123',
        }

        with patch('utils.views._setup_enduser') as setup_func:
            resp = self.client.post(self.join_url, payload)
            self.assertEqual(resp.status_code, 302)

            self.assertEqual(resp['Location'], "/join/?c=1")
            try:
                user = User.objects.get(email="new@example.com")
            except User.DoesNotExist:
                user = None
            self.assertIsNotNone(user)
            setup_func.assert_called_once_with(resp.wsgi_request, user)

    def test_get_signup_existing_enduser(self):
        """GET requests to join a program should redirect logged-in users to
        a confirmation page."""
        self.client.login(username="u", password="secret123")
        resp = self.client.get(self.join_url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], '/utils/signup/confirm-program/')
        self.client.logout()

    def test_post_signup_existing_enduser(self):
        """POSTing data for an *exisint* user account should redirect the user
        to the login url and display a message."""
        payload = {
            'email': 'u@example.com',
            'first_name': 'Existing',
            'last_name': 'User',
            'pw-password': 'secret123',
            'pw-password_confirmation': 'secret123',
        }

        resp = self.client.post(self.join_url, payload)
        self.assertEqual(resp.status_code, 302)
        redirect_url = "{}?next={}".format(
            reverse('login'), reverse('utils:confirm'))
        self.assertEqual(resp['Location'], redirect_url)

        # Follow the redirect & check for the message.
        resp = self.client.get(redirect_url)
        self.assertIn('messages', resp.context)
        self.assertEqual(
            [m.message for m in resp.context['messages']],
            ["It looks like you already have an account! Log in to continue."]
        )

    def test_get_confirm_joined_unathenticated(self):
        resp = self.client.get(self.confirm_url)
        self.assertEqual(resp.status_code, 302)

    def test_post_confirm_joined_unathenticated(self):
        payload = {'confirmed': '1'}
        resp = self.client.post(self.confirm_url, payload)
        self.assertEqual(resp.status_code, 302)

    def test_get_confirm_joined_athenticated(self):
        """When an existing, authenticated users visits the join url, they
        should be redirected to a confirmation page."""
        # 1. Login with an existing user, then GET the /join/ url
        self.client.login(username="u", password="secret123")
        resp = self.client.get(self.join_url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], self.confirm_url)

        # 2. It should redirect to the confirm page, so GET that...
        resp = self.client.get(self.confirm_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "utils/confirm_join.html")

        # 3. Verify context
        self.assertIn('organization', resp.context)
        self.assertIn('program', resp.context)
        self.assertIn('confirmed', resp.context)
        self.assertEqual(resp.context['organization'], self.organization)
        self.assertEqual(resp.context['program'], self.program)

        self.client.logout()

    def test_post_confirm_joined_athenticated(self):
        """When an existing, authenticated users submits a confirmation, the
        `utils.views._setup_enduser` function should get called and they should
        get redirected back to the page with a confirmation token."""

        # 1. Set a session variable, which should have gotten set previously.
        self.client.login(username="u", password="secret123")
        self.client.session['organization'] = self.organization.id
        self.client.session['program'] = self.program.id

        # 2. Submit the payload / confirmation
        with patch('utils.views._setup_enduser') as setup_func:
            resp = self.client.post(self.confirm_url, {'confirmed': "1"})
            self.assertEqual(resp.status_code, 302)
            setup_func.assert_called_once_with(
                resp.wsgi_request,
                self.user,
                send_welcome_email=False
            )
            self.assertIsNone(self.client.session.get('organization'))
            self.assertIsNone(self.client.session.get('program'))

        # 3. Inspect the response, and follow the redirect
        redirect_url = self.confirm_url + "?confirmed=1"
        self.assertEqual(resp['Location'], redirect_url)
        resp = self.client.get(redirect_url)
        self.assertTrue(resp.context['confirmed'])
