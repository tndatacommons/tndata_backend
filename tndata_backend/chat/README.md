Chat
====

A chat app based on websockets (using django channels).

----

## Connecting to the websocket

When you connect to the websocket, you need to specify a *user* and a *room*.

There are three supported ways to specify a room, and the backend will look
for these in this order:

1. Connect to `wss://app.tndata.org/chat/`
   (or `wss://staging.tndata.org/chat/`, etc), and include an `x-room` header
   on the request. That will specify which room the user should be connected to.
   (e.g. `x-room: chat-1-995`)
2. Include a query string parameter on the connection url. e.g.
   `wss://app.tndata.org/chat/?room=chat-1-995`
3. If neither of the above are supplied, a room name will be constructed from
   the URL path used during connection. Any path information, e.g. for 1-1 chat
   rooms between a logged-in user and a path-defined user, like `/chat/USERID/`.
   (e.g. `wss://app.tndata.org/chat/995/`).

To specify the user connected, include the TNData API token while connecting:

1. Include the user's API auth token as a query string paramter when connecting
   to the websocket, e.g. `wss://app.tndata.org?token=API_TOKEN`, or
2. Include the API auth token as part of the header when connection to the
   websocket: `authorization: token API_TOKEN`


## Sending/Receiving messages.

To send a message, construct the following JSON-encoded string, and send it
over the websocket.

    {
        'text': "Text of message",
        'from': <User ID of the sender>,    // optional
        'token': <API Token of the sender>  // optional
    }

The *optional* `from` and `token` fields allow you identify your user in
each message sent.

When successfully sent, you will receive a copy of all messages sent over
the websocket (including your own) as a JSON-formatted string. For example:

    {
      "from_id": "42",
      "from": "Brad Montgomery",
      "message": "Hello World! This is the message to display."
      "avatar": "//lh5.googleusercontent.com/.../photo.jpg",
      "digest": "584d07235fb9e4f2ab2a2c0c24142180",
    }

Sometimes you will receive `system` messages. Those are just informative (e.g.
when a user connects / disconnects, etc). They'll typically look like this:

    {
        'from_id': '',
        'from': 'system',
        'room': 'chat-1-995',
        'message': "Soandso joined."
    }

You should recieve these kinds of messages when a user connects or disconnects
from the websocket.


## Read Receipts

The digest embedded within a message is a unique identifier for that message.
This allows us to mark a message as read whenever you receive it. Upon
receiving a message from someone, you can mark it as read by sending the
following message back over the websocket:

    {
        "received": "584d07235fb9e4f2ab2a2c0c24142180"
    }

This will notifiy the chat backend that the message has been received, and it
will (eventually) be marked at read.


## Chat API endpoints.

In addition to the websocket communication, the following RESTful apis exist
to support additional chat-related features.

See [app.tndata.org/api/chat/](https://app.tndata.org/api/chat/) for further
documentation, but this api supports the following:

- Retrieve a User's Chat Messages
- Retrieve a user's unread messages
- Retrieve individual ChatMessage objects
- Retrive chat room history
- Mark an entire chat room's messages as read.

## Misc resources

While working in DEBUG mode or in [staging](https://app.tndata.org/chat/debub/),
there is a debug panel / log of all chat websocket traffic.

