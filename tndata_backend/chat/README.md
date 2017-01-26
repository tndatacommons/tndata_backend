Chat
====

A chat app based on websockets (using django channels).

____

_Here are docs I wrote in slack; these need to be updated._



Update #4: We now have a debug panel for all chat websocket traffic (for staging only). You can see it at https://staging.tndata.org/chat/debug/
Update #3: See the udpated message format (#5 below) and the section on Read Receipts below.
Update #2: Review the formats of data you'll send and receive below (#4 & #5).
Update: We now also have an API endpoint for chat messages (read the docs there): https://app.tndata.org/api/chat/. These endpoints give you tools for retrieving a batch of messages at a time (e.g. for a chat room's history).

----

There's not really an api, since everything happens over a websocket. Here's what you need to know (or at least most of what I can think of):

1. Connect to `wss://staging.tndata.org` (or `wss://app.tndata.org`, etc).
   There are two ways to authenticate:
    - Include the user's API auth token as a query string paramter, i.e.
      `?token=YOUR_TNDATA_API_TOKEN_HERE` , or
    - Include the API auth token as part of the header when connection to the
      websocket: `authorization: token YOUR_TNDATA_API_TOKEN`
2. You can use the URL path to specify a chat room (that is a person-to-person
   message; think of an SMS message). So, sending a message to
   `wss://staging.tndata.org/chat/1/` will send a message to the user whose
   user ID is 1. (from the logged-in user)
3. To send a message, construct the following JSON-encoded string, and send it
   over the websocket. `{'text': "Text of message", "from": User ID, "token": User TOKEN"}`
4. You will receive messages in JSON. They'll look like this:

    {
      "from_id": "42",
      "avatar": "//lh5.googleusercontent.com/.../photo.jpg",
      "from": "Brad Montgomery",
      "message": "Hello World!"
      "digest": "584d07235fb9e4f2ab2a2c0c24142180",
    }

Sometimes you will receive `system` messages. Those are just informative (e.g.
when a user connects / disconnects, etc). In that case see the value
`from: "system"` in the message payload.

## Read Receipts

The digest embedded within a message is (highly-likely) a unique identifier for
that message. This allows us to mark a message as read whenever you receive it.
Upon receiving a message, just send another message back over the websocket with
the following format:

    {
        "received": "584d07235fb9e4f2ab2a2c0c24142180" // received msg's digest
    }

This will notifiy the chat backend that the message has been received, and it
will (eventually) be marked at read.

