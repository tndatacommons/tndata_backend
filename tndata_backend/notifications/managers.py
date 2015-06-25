import logging
from datetime import datetime
from django.db import IntegrityError, models, transaction


logger = logging.getLogger("loggly_logs")


class QuestionManager(models.Manager):

    def available(self, *args, **kwargs):
        qs = self.get_queryset()
        return qs.filter(available=True)


class GCMMessageManager(models.Manager):

    def expired(self, *args, **kwargs):
        """Return a queryset of expired messages."""
        return self.get_queryset().filter(expire_on__lte=datetime.utcnow())

    def ready_for_delivery(self, *args, **kwargs):
        """Return a queryset of messages that are ready to be delivered."""
        return self.get_queryset().exclude(success=True).filter(
            success=None,  # doen't re-send failed messages
            deliver_on__lte=datetime.utcnow()
        )

    def create(self, user, title, message, deliver_on, obj=None):
        """Creates an instance of a GCMMessage. Requires the following data:

        * user: an auth.User instance.
        * title: Title of the Message.
        * message: Content of the Message.
        * deliver_on: A datetime object: When the message will be delivered (UTC)
        * obj: (optional) An object to which this message will be related.

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
            msg = None  # Most likely a duplicate error.
        return msg
