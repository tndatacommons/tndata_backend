from datetime import datetime
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .settings import (
    DEFAULT_BEHAVIOR_TRIGGER_NAME,
    DEFAULT_BEHAVIOR_TRIGGER_TIME,
    DEFAULT_BEHAVIOR_TRIGGER_RRULE,
)


class UserActionManager(models.Manager):

    def with_custom_triggers(self):
        """Returns a queryset of UserAction objets whose custom_trigger field
        meets the followign criteria:

        1. Is not null
        2. It's members (trigger_date/time/recurrences) are not all null

        """
        qs = self.get_queryset()
        return qs.filter(
            Q(custom_trigger__isnull=False) &
            Q(custom_trigger__time__isnull=False) &
            (
                Q(custom_trigger__recurrences__isnull=False) |
                Q(custom_trigger__trigger_date__isnull=False)
            )
        )

    def with_only_default_triggers(self):
        """Returns a queryset of UserAction objects that do NOT have a custom
        trigger, but whose Action does include a default (time) trigger."""
        qs = self.get_queryset()
        return qs.filter(
            custom_trigger__isnull=True,
            action__default_trigger__isnull=False,
            action__default_trigger__trigger_type="time"
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

    def create_for_user(self, user, name, time, date, rrule, obj=None):
        """Creates a time-type trigger based on the given RRule data."""
        # Ensure that we associate any new Triggers with a related object
        # (e.g. UserAction.custom_trigger?)

        trigger = self.create(
            user=user,
            name=name,
            trigger_type="time",
            time=time,
            trigger_date=date,
            recurrences=rrule,
        )

        if obj is not None and hasattr(obj, 'custom_trigger'):
            obj.custom_trigger = trigger
            obj.save(update_fields=['custom_trigger'])
            obj.save()
        return trigger


class WorkflowManager(models.Manager):
    """A simple model manager for those models that include a workflow
    `state` field. This adds a convenience method for querying published
    objects.

    """

    def published(self, *args, **kwargs):
        return self.get_queryset().filter(state='published')


class CategoryManager(WorkflowManager):
    """Updated WorkflowManager for Categories; we want to exclude packaged
    content from the list of published Categories."""

    def published(self, *args, **kwargs):
        qs = super().published()
        return qs.filter(packaged_content=False)

    def packages(self, *args, **kwargs):
        """Return only Categories that have been marked as packages.

        By default this returns only published categories; pass in
        `published=False` to return all packaged content.

            Category.objects.packages(published=False)

        """
        published = kwargs.pop("published", True)
        qs = super().get_queryset()
        if published:
            return qs.filter(packaged_content=True, state="published")
        else:
            return qs.filter(packaged_content=True)


class PackageEnrollmentManager(models.Manager):

    def enroll_by_email(self, email, categories):
        """Create enrollments for the given email address."""
        pass
