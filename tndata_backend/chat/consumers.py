import json

from channels import Channel, Group
from channels.sessions import enforce_ordering
from channels.auth import channel_session_user, channel_session_user_from_http

from django.contrib.auth import get_user_model
from django.utils.text import slugify
from .models import ChatMessage


def _get_user(message):
    """This function is used below and inspects wether the message includes
    an authenticated user, and if not, it tries to look up a user from the
    message's query_string (e.g. ?token=) ...

    TODO: also look at a header is see if we've got an auth token?
    TODO: There's probably a way to optimize this.

    Returns a User object.

    """
    if message.user.is_authenticated():
        return message.user

    User = get_user_model()
    try:
        # NOTE: this is the only query string object supportd.
        token = message.content.get('query_string').split("token=")[1]
        return User.objects.get(auth_token__key=token)
    except (KeyError, IndexError, AttributeError, User.DoesNotExist):
        pass
    return message.user


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

    # We may need to look up the user if they're not logged in.
    user = message.user
    if not user.is_authenticated() and 'user_id' in message.channel_session:
        User = get_user_model()
        user = User.objects.get(pk=message.channel_session['user_id'])

    try:
        name = user.username
        avatar = (
            user.userprofile.google_image.replace('https:', '').replace('http:', '')
            or '//www.gravatar.com/avatar/0?d=mm&s=30'
        )
    except AttributeError:
        name = "anonymous"
        avatar = '//www.gravatar.com/avatar/0?d=mm&s=30'

    payload = {
        'from': name,
        "message": "{}".format(message['text']),
        'avatar': avatar,
    }
    Group(room).send({'text': json.dumps(payload)})  # send to users for display

    # Now, send it to the channel to create the ChatMessage.
    Channel("create-chat-message").send({
        "room": room,
        "text": message['text'],
        "user_id": user.id,
    })


@enforce_ordering(slight=True)
@channel_session_user_from_http  # Give us session + user from http session.
def ws_connect(message):
    """Handles when clients connect to a websocket.
    Connected to the `websocket.connect` channel."""

    # Get the connected user.
    user = _get_user(message)

    # 1-1 chat rooms between a logged-in user and a path-defined user.
    # path will be something like `/chat/username/`
    try:
        path = message.content['path'].strip('/').split('/')[1]
    except IndexError:
        path = 'unknown'
    users = sorted([path, user.username])
    room = slugify("chat-{}-{}".format(*users))

    # Save room in session and add us to the group
    message.channel_session['room'] = room
    message.channel_session['user_id'] = user.id

    Group(room).add(message.reply_channel)

    payload = {
        'from': 'system',
        'message': "{} joined.".format(user),
    }
    Group(room).send({'text': json.dumps(payload)})


@enforce_ordering(slight=True)
@channel_session_user  # Gives us a session store + a user
def ws_disconnect(message):
    """Handles when clients disconnect from a websocket.
    Connected to the `websocket.disconnect` channel."""

    user = _get_user(message)

    # Pull the room from the channel's session.
    room = message.channel_session['room']

    payload = {
        'from': 'system',
        'message': "{} left.".format(user),
    }
    Group(room).send({'text': json.dumps(payload)})
    Group(room).discard(message.reply_channel)
