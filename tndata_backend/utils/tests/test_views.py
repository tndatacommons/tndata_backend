from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase

User = get_user_model()


class TestPasswordResetRequestView(TestCase):

    @classmethod
    def setUpTestData(cls):
        super(cls, TestPasswordResetRequestView).setUpTestData()
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
