import json
from pprint import pformat
from urllib.parse import parse_qs

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify

from django_rq import get_connection


def qs_as_dict(query_string):
    """Given a querysetring, parse it and return a flattened dict (i.e. only
    one value per key."""
    return {k: v[0] for k, v in parse_qs(query_string).items()}


def log_messages_to_redis(payload, key='websocket-debug'):
    """Log all websocket traffic for debugging purposes."""
    if settings.DEBUG or settings.STAGING:
        conn = get_connection('default')
        info = "{}|{}".format(timezone.now().strftime("%c"), pformat(payload))
        conn.lpush(key, info)


def decode_message_text(message):
    """Given a message, attempt to decode the JSON string and return the TEXT
    of the message (what the user should see).

    Returns a tuple of the type:

        (message_content, message_type)

    where message type is one of the following:

        - "message": This is a ChatMessage the user should see.
        - "receipt": This is a read-receipt message (not visible to the user)

    """
    try:
        received = json.loads(message.content['text'])
        if 'received' in received:
            return (received['received'], 'receipt')
        return (received['text'], 'message')
    except (IndexError, ValueError):  # wasnt' JSON-encoded?
        return message.content.get('text', '')


def generate_room_name(values):
    """Given an iterable of values that can either be strings or User objects,
    generate a chat room name.

    Usually, this will me a person-to-person chat room, so the format will
    be something like:  `chat-USERID-USERID`.

    """
    values = [str(v.id) if hasattr(v, 'id') else str(v) for v in values]
    values = sorted(values)
    return slugify("chat-{}".format('-'.join(values)))


def get_room(message, user):
    """
    Inspect the message to see what `room` it should be delivered to. This
    function is used when connecting to a websocket, and will look at the
    following, in this order (first match wins).

    - A header that specifies a room `X-ROOM: whatever`
    - A query string parameter: `?room=whatever`
    - Any path information, e.g. for 1-1 chat rooms between a logged-in user
      and a path-defined user, like `/chat/USERID/`

    During connections, the message.content payload looks like this:

        {'client': ['127.0.0.1', 54054],
         'headers': [[b'user-agent',
                      b'Mozilla/5.0 ...(KHTML, like Gecko)],
                     [b'x-forwarded-for', b'10.0.2.2'],
                     [b'connection', b'upgrade'],
                     [b'accept-encoding', b'gzip, deflate, sdch, br'],
                     [b'origin', b'http://localhost:3000'],
                     [b'upgrade', b'websocket'],
                     [b'x-room', b'chat-1-995']]
         'method': 'FAKE',
         'order': 0,
         'path': '/chat/995/',
         'query_string': 'room=chat-1-995',
         'reply_channel': 'websocket.send!JQAGEyzzMFqw',
         'server': ['127.0.0.1', 8000]}

    """
    # Look for a room in a header
    try:
        headers = [
            (k.decode('utf-8'), v.decode('utf-8'))
            for k, v in message.content['headers']
        ]
        headers = [v for k, v in headers if k.lower() == 'x-room']
        return headers[0][1].lower()  # Actual room name
    except (KeyError, IndexError, AttributeError):
        pass

    # Look up a 'room' query string parameter
    try:
        query_data = qs_as_dict(message.content['query_string'])
        return query_data['room']
    except (KeyError, ValueError):
        pass

    # construct a room name using the path
    try:
        path = message.content['path'].strip('/').split('/')[1]
        return generate_room_name((path, user))
    except IndexError:
        pass

    return None


def get_user_from_message(message):
    """This function inspects the content of a websocket message and attempts
    to return the User object who authored the message. There are serveral
    strategies for doing this:

    1. If `message.user` is an autenticated users, return it.
    2. See if the User's ID is stored in a channel session and look them up.
    3. Attempt to lookup an auth token stored in the message's query string
       or in the headers (available on websocket.connect)
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

    # 3a. Look for a token in a header
    token = None
    try:
        headers = [
            (k.decode('utf-8'), v.decode('utf-8'))
            for k, v in message.content['headers']
        ]
        headers = [v for k, v in headers if k.lower() == 'authorization']
        token = headers[0].split()[1]  # 'Token ACTUAL_TOKEN_STRING'
    except (KeyError, IndexError, AttributeError):
        pass

    # 3b. Look for a token in a query string
    try:
        # NOTE: this is the only query string object supported.
        query_data = qs_as_dict(message.content.get('query_string'))
        token = query_data["token"]
    except (KeyError, IndexError, AttributeError):
        pass

    try:
        if token:
            return User.objects.get(auth_token__key=token)
    except User.DoesNotExist:
        pass

    # 4. See if there's a token or ID in the message content.
    try:
        payload = json.loads(message.content.get('text', None))  # Poss. TypeError
        if 'token' in payload:
            return User.objects.get(auth_token__key=payload['token'])
        elif 'from' in payload and payload['from'].isnumeric():
            return User.objects.get(pk=payload['from'])
    except (TypeError, IndexError, ValueError, User.DoesNotExist):
        pass

    # Return None if we didn't find a user. Don't allow Anonymous Users.
    return None


def get_user_details(user):
    """Given a User, return a tuple of (name, avatar) for inclusion in
    a Chat Message payload."""
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
