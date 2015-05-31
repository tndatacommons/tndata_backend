Notifications
-------------

This app contains the things required to send Push notifications using
[Google Cloud Messaging](https://developer.android.com/google/gcm/index.html).
For more details, see: [Implementing a GCM Server](https://developer.android.com/google/gcm/server.html).

Settings
--------

This app exposes the following settings:

* `GCM` (required). A dictionary of Google Cloud Messaging settings. Currently,
  must contain an `API_KEY` entry.
* `NOTIFICATIONS` dictionary with any the following:
  * `DEFAULT_TITLE`: Default notification title
  * `DEFAULT_TEXT`: Default sub-text for notifications

Commands
--------

A few management commands make this app work. These should be scheduled to
run periodically.

* `send_messages` will send deliver messages. Should run every 5-10 minutes.
* `expire_messages` will remove previously delivered messages. Should run once a day.


Dependencies
------------

This app uses [pushjack](https://github.com/dgilland/pushjack).


GCM requirements
----------------

* Store client registration IDs
* Ability to generate unique Message IDs (Message IDs should be unique per sender ID.)
* Sends messages via HTTP:
    * Downstream-only: cloud-to-device messages.
    * Synchronous; sends a POST and waits for a response.
    * JSON or Plain Text.
* Requires the following info:
    * A Target: one or more `registration_id`s (up to 1000 for multicast) or...
    * a `notification_key` (for multiple devices owned by a single user)
    * Payload limit of 4096 bytes.
    * Collapsable Messages are stored by GCM for 4 weeks.
    * GCM will store up to 100 non-collapsible messages; others are discarded

