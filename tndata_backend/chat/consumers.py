"""
These consumers handle our chat communications over a websocket.



"""
import json

from channels import Channel, Group
from channels.sessions import enforce_ordering
from channels.auth import channel_session_user, channel_session_user_from_http

from django.contrib.auth import get_user_model
from .models import ChatMessage, generate_room_name

#from clog.clog import clog


def _get_user(message):
    """This function inspects the content of a message and attempts to return
    the User object who authored the message. There are serveral strategies
    for doing this:

    1. If `message.user` is an autenticated users, return it.
    2. See if the User's ID is stored in a channel session and look them up.
    3. Attempt to lookup an autho token stored in the message's query string
       (applicable when connecting to a channel)
    4. See if the message's content contains a JSON-encoded string with a
       token value.

    If any of the above succeed, this function returns a User object. Otherwise,
    it returns `message.user` which is probably an AnonymousUser object.

    """
    # 1. Return the authenticated user.
    if message.user and message.user.is_authenticated():
        return message.user

    User = get_user_model()

    # 2. Retrieve from channel session.
    if 'user_id' in message.channel_session:
        try:
            return User.objects.get(pk=message.channel_session['user_id'])
        except User.DoesNotExist:
            pass

    # 3. Look for a token in a query string
    try:
        # NOTE: this is the only query string object supported.
        token = message.content.get('query_string').split("token=")[1]
        return User.objects.get(auth_token__key=token)
    except (KeyError, IndexError, AttributeError, User.DoesNotExist):
        pass

    # 4. See if there's a token or ID in the message content.
    try:
        payload = json.loads(message.content['text'])
        if 'token' in payload:
            return User.objects.get(auth_token__key=payload['token'])
        elif 'from' in payload and payload['from'].isnumeric():
            return User.objects.get(pk=payload['from'])
    except (IndexError, ValueError, User.DoesNotExist):
        pass

    return message.user


def _get_user_details(user):
    """Return a tuple of (name, avatar)"""
    try:
        name = user.get_full_name()
        avatar = (
            user.userprofile.google_image.replace('https:', '').replace('http:', '')
            or '//www.gravatar.com/avatar/0?d=mm&s=30'
        )
    except AttributeError:
        name = "Anonymous"
        avatar = '//www.gravatar.com/avatar/0?d=mm&s=30'
    return (name, avatar)


def _decode_text(message):
    """Given a message, attempt to decode the JSON string and return the TEXT
    of the message (what the user should see)."""
    try:
        received = json.loads(message.content['text'])
        return received['text']
    except (IndexError, ValueError):  # wasnt' JSON-encoded?
        return message.content.get('text', '')


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

    # `message` attributes and info.
    # ------------------------------
    # message.channel - the channel object.
    # message.channel_layer -
    # message.channel_session - Sessions, but for channels.
    # message.content - dict of the stuff we're usually interested in:
    #   {
    #       'order': 1,
    #       'path': '/chat/995/',
    #       'reply_channel': 'websocket.send!fMCqdsWviiwR',
    #       'text': JSON-encoded string.
    #   }
    #clog(message.content, title="Message Content")

    # Stick the message on the processing queue (instead of sending
    # it directly to the group)
    room = message.channel_session['room']

    # Look up the user that sent the message
    user = _get_user(message)
    name, avatar = _get_user_details(user)

    # -------------------------------------------------------------------------
    # The following is the current format for our recieved data.
    # This needs to work for both the web app & mobile.
    #
    #  {
    #   text: text of the message,
    #   from: (optional) user ID of person sending it.
    #   token: OPTIONAL token
    #  }
    # -------------------------------------------------------------------------
    message_text = _decode_text(message)

    # Construct message sent back to the client.
    payload = {
        'from_id': user.id if user else '',
        'from': name,
        "message": "{}".format(message_text),
        'avatar': avatar,
    }

    Group(room).send({'text': json.dumps(payload)})  # send to users for display

    # Now, send it to the channel to create the ChatMessage object.
    Channel("create-chat-message").send({
        "room": room,
        "text": message_text,
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

    room = generate_room_name((path, user))

    # Save the room name and the user's ID in channel session sessions.
    message.channel_session['room'] = room
    message.channel_session['user_id'] = user.id

    Group(room).add(message.reply_channel)

    payload = {
        'from_id': '',
        'from': 'system',
        'message': "{} joined.".format(user.get_full_name() or user),
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
        'from_id': '',
        'from': 'system',
        'message': "{} left.".format(user.get_full_name() or user),
    }
    Group(room).send({'text': json.dumps(payload)})
    Group(room).discard(message.reply_channel)
