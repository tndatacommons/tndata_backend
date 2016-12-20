"""
This module defines routing for django `channels`.
"""
from channels.routing import route
from chat.consumers import ws_connect, ws_disconnect, ws_message
from chat.consumers import chat_message_consumer


channel_routing = [
    # This takes over all http requests.
    #route("http.request", "chat.consumers.http_consumer"),

    route("websocket.connect", ws_connect),
    route("websocket.receive", ws_message),
    route("websocket.disconnect", ws_disconnect),
    route("create-chat-message", chat_message_consumer),
]
