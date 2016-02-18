"""
Models for user-created, Custom Goals & Actions.

"""
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


from utils.user_utils import to_localtime, to_utc

from .progress import UserCompletedAction
from .triggers import Trigger
from ..managers import CustomActionManager


class CustomGoal(models.Model):
    """A user-created Goal."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        help_text="The user to which this goal belongs"
    )
    title = models.CharField(
        max_length=128,
        db_index=True,
        help_text="A title for your Goal."
    )
    title_slug = models.SlugField(max_length=128, db_index=True, editable=False)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_on', 'title']
        verbose_name = "Custom Goal"
        verbose_name_plural = "Custom Goals"

    def __str__(self):
        return "{0}".format(self.title)

    def save(self, *args, **kwargs):
        self.title_slug = slugify(self.title)
        super().save(*args, **kwargs)


class CustomAction(models.Model):
    """A user-created Action; This is their reminder."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        help_text="The user to which this action belongs."
    )
    customgoal = models.ForeignKey(
        CustomGoal,
        help_text="The custom goal to which this action belongs"
    )
    title = models.CharField(
        max_length=128,
        db_index=True,
        help_text="A title for your custom action"
    )
    title_slug = models.SlugField(max_length=128, db_index=True, editable=False)
    notification_text = models.CharField(
        max_length=256,
        help_text="The text that will be displayed in the app's push notification"
    )
    custom_trigger = models.ForeignKey(Trigger, blank=True, null=True)

    # The next/prev trigger dates operate exactly like those in UserAction
    next_trigger_date = models.DateTimeField(blank=True, null=True, editable=False)
    prev_trigger_date = models.DateTimeField(blank=True, null=True, editable=False)

    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_on', 'title']
        verbose_name = "Custom Action"
        verbose_name_plural = "Custom Actions"

    def __str__(self):
        return "{0}".format(self.title)

    def save(self, *args, **kwargs):
        self.title_slug = slugify(self.title)
        self._set_next_trigger_date()
        super().save(*args, **kwargs)

    @property
    def trigger(self):
        return self.custom_trigger

    @trigger.setter
    def trigger(self, value):
        self.custom_trigger = value

    @property
    def next_reminder(self):
        """Returns next_trigger_date in the user's local timezone."""
        if self.next_trigger_date is not None:
            return to_localtime(self.next_trigger_date, self.user)
        return self.next()

    def next(self):  # NOTE: Copy/pasted from UserAction.next
        """Return the next trigger datetime object in the user's local timezone
        or None. This method will either return the value of `next_trigger_date`
        or the next date/time generated from the trigger, whichever is *next*."""

        trigger_times = []
        if self.next_trigger_date and self.next_trigger_date > timezone.now():
            # Convert to the user's timezone.
            trigger_times.append(to_localtime(self.next_trigger_date, self.user))

        if self.trigger:
            trigger_times.append(self.trigger.next(user=self.user))

        trigger_times = list(filter(None, trigger_times))
        if len(trigger_times) > 0:
            return min(trigger_times)

        return None

    def _set_next_trigger_date(self):  # NOTE: UserAction._set_next_trigger_date
        """Attempt to  stash this action's next trigger date so we can query
        for it. This first tries any custom triggers then uses the default
        trigger. The result may be None (it's possible some action's no longer
        have a future trigger).

        NOTE: Always store this in UTC.

        """
        # ---------------------------------------------------------------------
        # NOTE: Some triggers have time, but no date or recurrence. These will
        # automatically generate a `next` value IFF the current time is before
        # the trigger's time; However, when these get queued up, it seems the
        # prev_trigger_date eventually gets overwritten. We need to figure out
        # how to write that value when it makes sense, given that triggers are
        # queued up every few minutes.
        # ---------------------------------------------------------------------
        trigger = self.trigger
        if trigger:
            # This trigger retuns the date in the user's timezone, so convert
            # it back to UTC.
            next_date = trigger.next(user=self.user)
            next_date = to_utc(next_date)

            # Save the previous trigger date, but don't overwrite on subsequent
            # saves; Only save when `next_trigger_date` changes (and is not None)
            next_changed = (
                next_date != self.next_trigger_date and
                next_date != self.prev_trigger_date
            )
            if next_changed and self.next_trigger_date:
                self.prev_trigger_date = self.next_trigger_date

            self.next_trigger_date = next_date

            # If we get to this point and the previous trigger is none,
            # try to back-fill (generate it) using the recurrence.
            if self.prev_trigger_date is None:
                prev = self.trigger.previous(user=self.user)
                self.prev_trigger_date = to_utc(prev)

            # If the prev trigger is *still* None, it's possible this is a
            # non-recurring event or that we've run out of recurrences. If
            # that's the case, and next is in the past, prev == next.
            in_past = (
                self.next_trigger_date and
                self.next_trigger_date < timezone.now()
            )
            if self.prev_trigger_date is None and in_past:
                self.prev_trigger_date = self.next_trigger_date

    def get_user_mapping(self, user):
        """When notifications are creaated, this method will be called to
        set an ID mapping this object back to a user. This is needed for
        goals.UserAction objects, but it's not relevant here, so set to -1.

        """
        return -1

    def queued_notifications(self):
        """Return a queryset of related GCMMessage objects. """
        ct = ContentType.objects.get_by_natural_key('goals', 'customaction')
        msgs = self.user.gcmmessage_set.filter(
            content_type=ct,
            object_id=self.id,
        )
        msgs = msgs.order_by('-deliver_on').distinct()
        return msgs

    objects = CustomActionManager()


class UserCompletedCustomAction(models.Model):
    """

    NOTE: This model is structured exactly like the one in
    models.progress.UserCompletedAction, except that it's FK's are links back
    to CustomAction (rather than a UserAction)

    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    customaction = models.ForeignKey(CustomAction)
    customgoal = models.ForeignKey(CustomGoal)
    state = models.CharField(
        max_length=32,
        default=UserCompletedAction.UNSET,
        choices=UserCompletedAction.STATE_CHOICES
    )
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{0}".format(self.customaction.title)

    class Meta:
        ordering = ['-updated_on', 'user', 'customaction']
        verbose_name = "User Completed Custom Action"
        verbose_name_plural = "User Completed Custom Actions"

    @property
    def uncompleted(self):
        return self.state == UserCompletedAction.UNCOMPLETED

    @property
    def completed(self):
        return self.state == UserCompletedAction.COMPLETED

    @property
    def dismissed(self):
        return self.state == UserCompletedAction.DISMISSED

    @property
    def snoozed(self):
        return self.state == UserCompletedAction.SNOOZED


class CustomActionFeedback(models.Model):
    """XXX: User-supplied feedback on how they're achieving their goals / what
    they're doing, etc?

    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    customgoal = models.ForeignKey(CustomGoal)
    customaction = models.ForeignKey(CustomAction)
    text = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{0}".format(self.customaction)

    class Meta:
        ordering = ['-created_on', 'user']
        verbose_name = "Custom Action Feedback"
        verbose_name_plural = "Custom Action Feedback"
