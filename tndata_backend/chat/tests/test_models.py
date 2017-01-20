from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import ChatMessage
from ..utils import generate_room_name


class TestChatMessageManager(TestCase):
    """Tests for `ChatMessageManager` manager."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user_a = User.objects.create_user("a", "a@a.com", "pass")
        cls.user_b = User.objects.create_user("b", "b@b.com", "pass")

        cls.message_1 = ChatMessage.objects.create(
            user=cls.user_a,
            room="chat-{}-{}".format(cls.user_a.id, cls.user_b.id),
            text="Message 1",
            read=True,
        )
        cls.message_2 = ChatMessage.objects.create(
            user=cls.user_b,
            room="chat-{}-{}".format(cls.user_a.id, cls.user_b.id),
            text="Message 2",
            read=True,
        )
        cls.message_3 = ChatMessage.objects.create(
            user=cls.user_a,
            room="chat-{}-{}".format(cls.user_a.id, cls.user_b.id),
            text="Message 3",
        )

    def test__unread(self):
        results = ChatMessage.objects.unread()
        self.assertEqual(results.count(), 1)
        self.assertEqual(results[0].text, 'Message 3')

    def test_to_user(self):
        expected = sorted([m.text for m in (self.message_1, self.message_3)])
        actual = ChatMessage.objects.to_user(self.user_b)
        actual = sorted(m.text for m in actual)
        self.assertListEqual(actual, expected)

    def test_for_users(self):
        expected = sorted([
            m.text for m in
            [self.message_1, self.message_2, self.message_3]
        ])
        actual = ChatMessage.objects.for_users((self.user_b, self.user_a))
        actual = sorted([m.text for m in actual])
        self.assertListEqual(actual, expected)

    def test_recent(self):
        messages = sorted([m.id for m in ChatMessage.objects.recent()])
        expected = sorted([self.message_1.id, self.message_2.id, self.message_3.id])
        self.assertListEqual(messages, expected)


class TestChatMessage(TestCase):
    """Tests for the `ChatMessage` model."""

    @classmethod
    def setUpTestData(cls):
        # Create a user.
        User = get_user_model()
        cls.user_a = User.objects.create_user("a", "a@a.com", "pass")
        cls.user_b = User.objects.create_user("b", "b@b.com", "pass")

        cls.message_1 = ChatMessage.objects.create(
            user=cls.user_a,
            room="chat-{}-{}".format(cls.user_a.id, cls.user_b.id),
            text="Message 1",
            read=True,
        )
        cls.message_2 = ChatMessage.objects.create(
            user=cls.user_b,
            room="chat-{}-{}".format(cls.user_a.id, cls.user_b.id),
            text="Message 2",
            read=True,
        )
        cls.message_3 = ChatMessage.objects.create(
            user=cls.user_a,
            room="chat-{}-{}".format(cls.user_a.id, cls.user_b.id),
            text="Message 3",
        )

    def test__str__(self):
        expected = "Message 1"
        actual = "{}".format(self.message_1)
        self.assertEqual(expected, actual)

    def test_generate_room_name(self):
        self.assertEqual(
            generate_room_name((self.user_a, self.user_b)),
            "chat-{}-{}".format(self.user_a.id, self.user_b.id)
        )

    def test_default_read_status_is_false(self):
        self.assertFalse(self.message_3.read)
