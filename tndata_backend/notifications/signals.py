import django.dispatch

# -----------------------------------------------------------------------------
#
# A signal that will be fired when a GCMMessage is snoozed. This will
# allow other apps to listen for this event, and take appropriate actions.
# The provided arguments include:
#
# - message: the GCMMessage instance
# - user: the User to whom the message would be delivered
# - related_object: The GCMMessage's content_object (if any)
# - deliver_on: The new delivery date for the message.
#
# -----------------------------------------------------------------------------

snooze_args = ['message', 'user', 'related_object', 'deliver_on']
notification_snoozed = django.dispatch.Signal(providing_args=snooze_args)
