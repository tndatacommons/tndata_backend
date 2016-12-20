from channels import Channel, Group
from channels.handler import AsgiHandler
from channels.sessions import channel_session, enforce_ordering
from channels.auth import http_session_user, channel_session_user, channel_session_user_from_http

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils.html import escape

from .models import ChatMessage

from clog.clog import clog

# TODO: figure out how to create rooms for 1-1 chat between 2 users. (do we need a Group?)
# TODO: figure out how to create a ChatMessage object for chats.
# TODO: ^^ how to retrive the user data so we can store that on the ChatMessage
# TODO: figure out how to auto-display the channel's last 10 messages or so.

def chat_message_consumer(message):
    """Given a message, this creates a DB object and sends the message to a group.

    The given message should have the following content:

        - user_id: ID of the user who created the message.
        - room: name of the room the message was sent to.
        - text: text of the message.

    """
    # Save the model
    try:
        User = get_user_model()
        user = User.objects.get(pk=message.content['user_id'])
        ChatMessage.objects.create(
            user=user,
            room=message.content['room'],
            text=message.content['text'],
        )
    except (User.DoesNotExist, KeyError) as e:
        clog(e, color='red')


@enforce_ordering(slight=True)
@channel_session_user  # Gives us a channel_session + user
def ws_message(message):
    """Handles received messages to a websocket."""
    # Stick the message on the processing queue (instead of sending
    # it directly to the group)
    room = message.channel_session['room']

    payload = {
        "text": "{}: {}".format(message.user.first_name, escape(message['text']))
    }
    Group(room).send(payload)  # send to users for display

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
    users = sorted([
        message.content['path'].strip('/').split('/')[1],
        message.user.username
    ])
    room = "chat-{}-{}".format(*users)

    # XXX: Interesting attributes on message.content
    # message.content['order']
    # message.content['path']  # e.g. /chat
    # message.content['query_string']
    # message.content['reply_channel']
    # connect_data = {
        # 'room': room,
        # 'user_id': message.user.id,
        # 'path': message.content['path'],
        # 'query_string': message.content['query_string'],
        # 'reply_channel': message.content['reply_channel'],
    # }
    # clog(connect_data, title="On Connection", color="magenta")

    # Save room in session and add us to the group
    message.channel_session['room'] = room
    Group(room).add(message.reply_channel)


@enforce_ordering(slight=True)
@channel_session_user  # Gives us a session store + a user
def ws_disconnect(message):
    """Handles when clients disconnect from a websocket.
    Connected to the `websocket.disconnect` channel."""

    # Pull the room from the channel's session.
    room = message.channel_session['room']
    Group(room).discard(message.reply_channel)
