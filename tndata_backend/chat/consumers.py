from channels import Group
from channels.handler import AsgiHandler
from channels.sessions import channel_session

from django.http import HttpResponse
from django.utils.html import escape

from clog.clog import clog


# TODO: -----------------------------------------------------------------------
# TODO: Pick up with Authentication in the docs:
# TODO: https://channels.readthedocs.io/en/stable/getting-started.html#authentication
# TODO: -----------------------------------------------------------------------


# Connected to websocket.connect
@channel_session
def ws_connect(message):
    # Work out room name from path (ignore slashes)
    room = message.content['path'].strip("/")

    clog(message, title="CONNECT", color="green")
    clog(room, title="Room", color="magenta")

    # Save room in session and add us to the group
    message.channel_session['room'] = room
    Group("chat-%s" % room).add(message.reply_channel)


# Connected to websocket.receive
@channel_session
def ws_message(message):
    room = message.channel_session['room']

    clog(message.content, title="[{}] message content".format(room))
    Group("chat-%s" % room).send({
        "text": "{}".format(escape(message['text'])),  # message.content['text']?
    })


# Connected to websocket.disconnect
@channel_session
def ws_disconnect(message):
    clog(message, title="DISCONNECT", color="red")
    #Group("chat").discard(message.reply_channel)
    Group("chat-%s" % message.channel_session['room']).discard(message.reply_channel)
