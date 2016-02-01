import logging

from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, models, transaction
from django.db.models import Q
from django.utils import timezone

from . import queue

logger = logging.getLogger("loggly_logs")


class GCMMessageManager(models.Manager):

    def for_model(self, model_name, include_null=False):
        qs = self.get_queryset()
        if include_null:
            qs = qs.filter(Q(content_type__model=model_name) | Q(content_type=None))
        else:
            qs = qs.filter(content_type__model=model_name)
        return qs

    def expired(self, *args, **kwargs):
        """Return a queryset of expired messages."""
        return self.get_queryset().filter(expire_on__lte=timezone.now())

    def ready_for_delivery(self, *args, **kwargs):
        """Return a queryset of messages that are ready to be delivered."""
        return self.get_queryset().exclude(success=True).filter(
            success=None,  # doen't re-send failed messages
            deliver_on__lte=timezone.now()
        )

    def _message_exists(self, user, title, message, deliver_on, obj, content_type):
        """Check to see if a GCMMessage already exists; used to prevent creating
        duplicate messages.

        Return True or False.

        """
        criteria = {
            'user': user,
            'title': title,
            'message': message,
            'deliver_on': deliver_on,
            'object_id': obj.id if obj else None,
            'content_type': content_type,
        }
        # If there's a provided object, use it's content_type (which may be None)
        if obj:
            ct = ContentType.objects.get_for_model(obj.__class__)
            criteria['content_type'] = ct
        return self.filter(**criteria).exists()

    def create(self, user, title, message, deliver_on, obj=None, content_type=None):
        """Creates an instance of a GCMMessage. Requires the following data:

        * user: an auth.User instance.
        * title: Title of the Message.
        * message: Content of the Message.
        * deliver_on: A datetime object: When the message will be delivered (UTC)

        The following are optional keyword arguments:

        * obj: An object to which this message will be related.
        * content_type: A `ContentType` to which this message will be related.

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
            args = (user, title, message, deliver_on, obj, content_type)
            if not self._message_exists(*args):
                # Convert any times to UTC
                if timezone.is_naive(deliver_on):
                    deliver_on = timezone.make_aware(deliver_on, timezone.utc)

                kwargs = {
                    'user': user,
                    'title': title,
                    'message': message,
                    'deliver_on': deliver_on,
                }
                if content_type is not None:
                    kwargs['content_type'] = content_type
                if obj is not None:
                    kwargs['content_object'] = obj

                with transaction.atomic():
                    msg = self.model(**kwargs)
                    msg.save()

                # Enqueue it!
                queue.enqueue(msg)

                log_msg = "Created GCMMessage (id = %s) for delivery on: %s"
                logger.info(log_msg, msg.id, deliver_on)
        except IntegrityError:
            log_msg = (
                "Could not create GCMMessage for user (id = %s) and "
                "obj = %s. Possibly Duplicate."
            )
            logger.warning(log_msg, user, obj)
            msg = None  # Most likely a duplicate error.
        return msg
