import django.dispatch
import waffle

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from badgify.models import Award

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

# -----------------------------------------------------------------------------
# Badgify-related signal handlers.
# -----------------------------------------------------------------------------


@receiver(post_save, sender=Award, dispatch_uid='badgify-award-ccreated')
def badgify_award_created_send_notfication(sender, **kwargs):
    """When a user is awarded a badge, we listen for Award.post_save, then
    queue up a push notification for that award."""

    created = kwargs.get('created', False)
    award = kwargs.get('instance', False)

    if created and award and waffle.switch_is_active('enable-badgify'):
        from .models import GCMMessage
        GCMMessage.objects.create(
            user=award.user,
            title=award.badge.name,
            message=award.badge.description,
            deliver_on=timezone.now(),
            obj=award,
            priority=GCMMessage.HIGH
        )
