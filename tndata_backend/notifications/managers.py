import logging
from datetime import datetime
from django.db import IntegrityError, models, transaction
from django.utils import timezone


logger = logging.getLogger("loggly_logs")


class GCMMessageManager(models.Manager):

    def expired(self, *args, **kwargs):
        """Return a queryset of expired messages."""
        return self.get_queryset().filter(expire_on__lte=timezone.now())

    def ready_for_delivery(self, *args, **kwargs):
        """Return a queryset of messages that are ready to be delivered."""
        return self.get_queryset().exclude(success=True).filter(
            success=None,  # doen't re-send failed messages
            deliver_on__lte=timezone.now()
        )

    def _message_exists(self, user, title, message, deliver_on, obj):
        """Check to see if a GCMMessage already exists; used to prevent creating
        duplicate messages.

        Return True or False.

        """
        criteria = {
            'user': user,
            'title': title,
            'message': message,
            'deliver_on': deliver_on,
            'object_id': None,
        }
        if obj:  # If there's a provided object, also check it's content_type
            criteria.update({
                'object_id': obj.id,
                'content_type__model': obj.__class__.__name__.lower(),
            })

        return self.filter(**criteria).exists()

    def create(self, user, title, message, deliver_on, obj=None):
        """Creates an instance of a GCMMessage. Requires the following data:

        * user: an auth.User instance.
        * title: Title of the Message.
        * message: Content of the Message.
        * deliver_on: A datetime object: When the message will be delivered (UTC)
        * obj: (optional) An object to which this message will be related.

        This method first checks for duplicates, and will not create a duplicate
        version of a message.

        Note: This command will fail if the user has not registered a GCMDevice
        with a `GCMDevice.DoesNotExist` exception.

        If for some reason the Message could not be created (e.g. you tried
        to create a duplicate), this method will return `None`.

        """
        msg = None  # Our new GCMMessage object

        if not user.gcmdevice_set.exists():
            raise user.gcmdevice_set.model.DoesNotExist(
                "Users must have a registered Device before sending messages"
            )

        try:
            # Don't create Duplicate messages:
            if not self._message_exists(user, title, message, deliver_on, obj):
                # Convert any times to UTC
                if timezone.is_naive(deliver_on):
                    deliver_on = timezone.make_aware(deliver_on, timezone.utc)

                kwargs = {
                    'user': user,
                    'title': title,
                    'message': message,
                    'deliver_on': deliver_on,
                }
                if obj is not None:
                    kwargs['content_object'] = obj
                with transaction.atomic():
                    msg = self.model(**kwargs)
                    msg.save()

                log_msg = "Created GCMMessage (id = %s) for delivery on: %s"
                logger.info(log_msg, msg.id, deliver_on)
        except IntegrityError:
            log_msg = (
                "Could not create GCMMessage for user (id = %s) and "
                "obj = %s. Possibly Duplicate."
            )
            logger.info(log_msg, user, obj)
            msg = None  # Most likely a duplicate error.
        return msg
