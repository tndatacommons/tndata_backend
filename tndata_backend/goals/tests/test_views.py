from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import Client, TestCase


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
