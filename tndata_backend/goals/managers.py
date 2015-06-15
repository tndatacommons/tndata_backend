from datetime import datetime
from django.db import models
from django.utils import timezone

from .settings import (
    DEFAULT_BEHAVIOR_TRIGGER_NAME,
    DEFAULT_BEHAVIOR_TRIGGER_TIME,
    DEFAULT_BEHAVIOR_TRIGGER_RRULE,
)


class TriggerManager(models.Manager):
    """A simple manager for the Trigger model. This class adds a few convenience
    methods to the regular api:

    * get_default_behavior_trigger() -- returns the default trigger for
      `Behavior` reminders.
    * custom() -- the set of Triggers that are associated with a user
    * default() -- the set of default Triggers (not associated with a user)
    * for_user(user) -- returns all the triggers for a specific user.

    """

    def get_default_behavior_trigger(self):
        """Retrieve (or create) the default Behavior trigger.
        """
        try:
            return self.default().get(name_slug="default-behavior-reminder")
        except self.model.DoesNotExist:
            trigger_time = datetime.strptime(DEFAULT_BEHAVIOR_TRIGGER_TIME, "%H:%M")
            trigger_time = trigger_time.time().replace(tzinfo=timezone.utc)
            return self.model.objects.create(
                name=DEFAULT_BEHAVIOR_TRIGGER_NAME,
                trigger_type="time",
                time=trigger_time,
                recurrences=DEFAULT_BEHAVIOR_TRIGGER_RRULE,

            )

    def custom(self, **kwargs):
        """Returns the set of *custom* triggers; i.e. those that are associated
        with a User."""
        if 'user' not in kwargs:
            kwargs.update({'user__isnull': False})
        return self.get_queryset().filter(**kwargs)

    def default(self, **kwargs):
        """Returns the set of *default* triggers; i.e. those not associated
        with a User."""
        kwargs.update({'user': None})
        return self.get_queryset().filter(**kwargs)

    def for_user(self, user):
        """Allow queries like:

        Trigger.objects.for_user(some_user)

        """
        return self.get_queryset().filter(user=user)

    def create_for_user(self, user, name, time, rrule):
        """Creates a time-type trigger based on the given RRule data."""
        return self.create(
            user=user,
            name=name,
            trigger_type="time",
            time=time,
            recurrences=rrule,
        )


class WorkflowManager(models.Manager):
    """A simple model manager for those models that include a workflow
    `state` field. This adds a convenience method for querying published
    objects.

    """

    def published(self, *args, **kwargs):
        return self.get_queryset().filter(state='published')
