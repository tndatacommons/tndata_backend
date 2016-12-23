import json

from channels import Channel, Group
from channels.sessions import enforce_ordering
from channels.auth import channel_session_user, channel_session_user_from_http

from django.contrib.auth import get_user_model
from .models import ChatMessage


def chat_message_consumer(message):
    """Given a message, this creates a DB object and sends the message to a group.

    The given message should have the following content:

        - user_id: ID of the user who created the message.
        - room: name of the room the message was sent to.
        - text: text of the message.

    """
    try:
        User = get_user_model()
        user = User.objects.get(pk=message.content['user_id'])
        room = message.content['room']
        text = message.content['text']
        ChatMessage.objects.create(user=user, room=room, text=text)

    except (User.DoesNotExist, KeyError):
        pass  # TODO: log this


@enforce_ordering(slight=True)
@channel_session_user  # Gives us a channel_session + user
def ws_message(message):
    """Handles received messages to a websocket."""
    # Stick the message on the processing queue (instead of sending
    # it directly to the group)
    room = message.channel_session['room']

    try:
        name = message.user.username
    except AttributeError:
        name = "anonymous"

    payload = {
        'from': name,
        "message": "{}".format(message['text']),
    }
    Group(room).send({'text': json.dumps(payload)})  # send to users for display

    # Now, send it to the channel to create the ChatMessage.
    Channel("create-chat-message").send({
        "room": room,
        "text": message['text'],
        "user_id": message.user.id,
    })


@enforce_ordering(slight=True)
@channel_session_user_from_http  # Give us session + user from http session.
def ws_connect(message):
    """Handles when clients connect to a websocket.
    Connected to the `websocket.connect` channel."""

    # 1-1 chat rooms between a logged-in user and a path-defined user.
    # path will be something like `/chat/username/`
    try:
        path = message.content['path'].strip('/').split('/')[1]
    except IndexError:
        path = 'unknown'
    users = sorted([path, message.user.username])
    room = "chat-{}-{}".format(*users)

    # Save room in session and add us to the group
    message.channel_session['room'] = room
    Group(room).add(message.reply_channel)

    payload = {
        'from': 'system',
        'message': "{} joined.".format(message.user),
    }
    Group(room).send({'text': json.dumps(payload)})


@enforce_ordering(slight=True)
@channel_session_user  # Gives us a session store + a user
def ws_disconnect(message):
    """Handles when clients disconnect from a websocket.
    Connected to the `websocket.disconnect` channel."""

    # Pull the room from the channel's session.
    room = message.channel_session['room']

    payload = {
        'from': 'system',
        'message': "{} left.".format(message.user),
    }
    Group(room).send({'text': json.dumps(payload)})
    Group(room).discard(message.reply_channel)
