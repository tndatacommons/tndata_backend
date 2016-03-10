"""
The Trigger model encapsulates reminder schedules & information.

"""
import pytz
import random

from datetime import datetime, timedelta

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import ObjectDoesNotExist
from django.utils.text import slugify
from django.utils import timezone

from dateutil.relativedelta import relativedelta
from recurrence import serialize as serialize_recurrences
from recurrence.fields import RecurrenceField
from utils.user_utils import local_day_range, to_localtime, user_timezone

from ..managers import TriggerManager


class Trigger(models.Model):
    """Definition for a (possibly recurring) reminder for an user's Actions.

    A Trigger consists of one or more of the following:

    - A date and/or time when a notification should be sent.
    - Recurrences: How frequently (every day, once a month, etc) should the
      notification be sent.
    - Whether or not trigger should stop once the action has been completed.

    This model is heavily based on django-recurrence:
    https://django-recurrence.readthedocs.org

    """
    TOD_CHOICES = (
        ('early', 'Early Morning'),
        ('morning', 'Mid-Late Morning'),
        ('noonish', 'Around Noon'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
        ('late', 'During the night'),
    )
    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Once a week'),
        ('biweekly', 'A couple times a week'),
        ('multiweekly', 'Three - four times a week'),
        ('weekends', 'During the weekend'),
        ('monthly', 'Once a month'),
    )
    RELATIVE_UNIT_CHOICES = (
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        help_text="A Custom trigger, created by a user."
    )
    name = models.CharField(
        max_length=128,
        blank=True,
        db_index=True,
        help_text="A human-friendly name for this trigger"
    )
    name_slug = models.SlugField(max_length=128, blank=True, db_index=True)

    # Automatic/Dynamic delivery options
    # ----------------------------------
    time_of_day = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        choices=TOD_CHOICES,
        help_text="Select a time of day, and a notification will be sent at "
                  "some point during that time."
    )
    frequency = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        choices=FREQUENCY_CHOICES,
        help_text="Select a frequency to determine how often a reminder "
                  "should be sent."
    )

    # Specific Delivery options
    # -------------------------
    time = models.TimeField(
        blank=True,
        null=True,
        help_text="Time the trigger/notification will fire, in 24-hour format."
    )
    trigger_date = models.DateField(
        blank=True,
        null=True,
        help_text="A starting date for a recurrence, or a single date for a "
                  "one-time trigger."
    )
    recurrences = RecurrenceField(
        null=True,
        blank=True,
        help_text="An iCalendar (rfc2445) recurrence rule (an RRULE)"
    )
    start_when_selected = models.BooleanField(
        default=False,
        help_text="Should this trigger start on the day the user selects the "
                  "action? "
    )
    stop_on_complete = models.BooleanField(
        default=False,
        help_text="Should reminders stop after the action has been completed?"
    )
    disabled = models.BooleanField(
        default=False,
        db_index=True,
        help_text="When disabled, a Trigger will stop generating new events."
    )

    # Relative reminders examples:
    #
    # - 1 day after action selected
    # - 2 weeks after action selected
    # - 1 year after action selected
    #
    # IDEA: Once a user selects an action with a 'relative' reminder, we
    # immediately turn it into a custom reminder and pre-fill the `trigger_date`
    # based on when the UserAction instance is created. This will require
    # that the newly created UserAction instance know how to modify the trigger
    # accordingly. See the create_relative_reminder signal handler for UserAction
    relative_value = models.IntegerField(default=0)
    relative_units = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        choices=RELATIVE_UNIT_CHOICES,
    )

    def __str__(self):
        if self.is_dynamic:
            result = "{} in the {}".format(
                self.get_frequency_display(),
                self.get_time_of_day_display()
            )
            return result

        result = "{}".format(self.name if self.name else "Unnamed Trigger")
        if self.time:
            result = "{}\n{}".format(result, self.time)
        if self.trigger_date:
            result = "{}\n{}".format(result, self.trigger_date)
        if self.recurrences:
            result = "{}\n{}".format(result, self.recurrences_as_text())
        if self.is_relative and self.relative_value:
            result = "{}\nStarts {} {} after selection".format(
                result, self.relative_value, self.relative_units)
        elif self.is_relative:
            result = "{}\nStarts when selected".format(result)
        if self.stop_on_complete:
            result = "{}\nStops when complete".format(result)
        return result

    class Meta:
        ordering = ['disabled', 'name', 'id']
        verbose_name = "Trigger"
        verbose_name_plural = "Triggers"
        permissions = (
            ("view_trigger", "Can view Triggers"),
            ("decline_trigger", "Can Decline Triggers"),
            ("publish_trigger", "Can Publish Triggers"),
        )

    def _localize_time(self):
        """Adds the UTC timezone info to self.time."""
        if self.time and self.time.tzinfo is None:
            self.time = pytz.utc.localize(self.time)

    def _strip_rdate_data(self):
        """Our android recurrence dialog doesn't like RDATE rules as part of
        the recurrence; Additionally, we've saved that information as a separate
        field within this model, so let's strip out any RDATE rules.

        """
        rrule = self.serialized_recurrences()
        if rrule and 'RDATE:' in rrule:
            self.recurrences = rrule.split('RDATE:')[0].strip()

    def get_absolute_url(self):
        return reverse('goals:trigger-detail', args=[self.pk])

    def save(self, *args, **kwargs):
        """Always slugify the name prior to saving the model."""
        self.name_slug = slugify(self.name)
        self._localize_time()
        self._strip_rdate_data()
        super(Trigger, self).save(*args, **kwargs)

    @property
    def is_dynamic(self):
        return all([bool(self.time_of_day), bool(self.frequency)])

    def dynamic_trigger_date(self, user=None):
        random.seed()  # Seed our generator...
        # ---------------------------------------------------------------------
        # TODO: generate a dynamic trigger date based on the values for:
        # - time of day
        # - frequency
        # ---------------------------------------------------------------------
        # this is all fine, but...
        #
        # 1. We only queue up notifications 24-hours in advance. So the further
        #    dates will always get ignored.
        # 2. This is based on "now". So every time it's run it'll schedule a
        #    weekly item 7 days away (which would never go out)
        # 3. Can I use probabilities instead to determine if the thing should
        #    be scheduled today|tomorrow
        # ---------------------------------------------------------------------

        if not self.is_dynamic:
            return None

        user = user or self.user
        if user is None:
            raise AssertionError("Dynamic triggers require a user")

        # We need to an hour that corresponds to the selected Time of Day
        hours = {
            'early': [6, 7, 8],
            'morning': [9, 10, 11],
            'noonish': [11, 12, 13],
            'afternoon': [13, 14, 15, 16, 17],
            'evening': [17, 18, 19, 20, 21],
            'late': [22, 23, 0, 1, 2],
        }
        hour = random.choice(hours[self.time_of_day])
        minute = random.choice(range(1, 59))

        # We need a current time, and we need to know if it's the weekend.
        today = timezone.now()
        is_weekend = today.isoweekday() in [5, 6, 7]  # Fri, Sat, Sun

        # Probability that a message should be delivered today.
        probabilities = {
            'daily': 0.95,       # 95% chance it fires today
            'weekly': 1/7,       # 1/7 chance.
            'biweekly': 2/7,     # 2/7 chance.
            'multiweekly': 3/7,  # 3/7 chance.
            'weekends': 0.5 if is_weekend else 0,  # 50% chance on weekends.
            'monthly': 1 / 30,  # 1 / 30 chance
        }

        # XXX: If we run this method several times a day, are these values
        # still accurate (I think not); we need to divide by the number of times
        # we call this method / day?
        if random.random() < (probabilities[self.frequency] / 1440):
            # Create a date for "tomorrow"; include our hour/minute
            dt = today + timedelta(days=1)
            dt = dt.replace(hour=hour, minute=minute)
            return dt
        return None

    @property
    def is_relative(self):
        return (
            self.start_when_selected or
            all([self.relative_units, self.relative_value])
        )

    def relative_trigger_date(self, dt):
        """If this is a custom (has a user), relative trigger (has both a
        relative_value and relative_units or is a `start_when_selected` trigger),
        this method will calculate the trigger_date (when this trigger should
        start) relative to the given datetime object.

        Returns a datetime object or None.

        """
        if self.user and self.is_relative and self.relative_units:
            # build kwargs, e.g.: relativedelta(dt, months=5)
            kwargs = {self.relative_units: self.relative_value}
            return dt + relativedelta(**kwargs)
        elif self.user and self.is_relative and self.start_when_selected:
            # If it's just a "start when selected", return the give time.
            return dt
        return None

    def serialized_recurrences(self):
        """Return a rfc2445 formatted unicode string."""
        if self.recurrences:
            return serialize_recurrences(self.recurrences)
        else:
            return None

    def recurrences_as_text(self):
        if self.recurrences:
            result = ''
            rules = []
            # check all the recurrence rules
            for rule in self.recurrences.rrules:
                rules.append(rule.to_text())
            # also check for exclusion rules
            for exrule in self.recurrences.exrules:
                rules.append("Exclusions: {0}".format(exrule.to_text()))
            result = ", ".join(rules)
            if len(self.recurrences.rdates) > 0:
                result += " on "
                result += ", ".join(
                    ["{0}".format(d) for d in self.recurrences.rdates]
                )
            return result
        return ''

    def _combine(self, a_time, a_date=None, tz=None):
        """Combine a date & time into an timezone-aware datetime object.
        If the date is None, the current date (in either utc or the user's
        local time) will be used."""
        if tz is None:
            tz = self.get_tz()

        if a_date is None:
            a_date = timezone.now().astimezone(tz)

        # Ensure our combined date/time has the appropriate timezone
        if timezone.is_aware(a_time) and a_time.tzinfo != tz:
            # the time value here is correct, but should
            # be in the user's timezone.
            a_time = a_time.replace(tzinfo=None)

        dt = datetime.combine(a_date, a_time)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone=tz)
        elif timezone.is_aware(dt) and tz is not None:
            dt = dt.astimezone(tz)

        return dt

    def get_tz(self, user=None):
        """Return a Timezone object for the user; defaults to UTC if no user."""
        user = user or self.user
        if user:
            return pytz.timezone(user_timezone(user))
        return timezone.utc

    def get_alert_time(self, tz=None):
        """Return a datetime object (with appropriate timezone) for the
        starting date/time for this trigger."""
        if tz is None:
            tz = self.get_tz()
        alert_time = None
        if self.trigger_date and self.time:
            alert_time = self._combine(self.time, self.trigger_date, tz)
        elif self.time is not None:
            now = timezone.now().astimezone(tz)
            alert_time = self._combine(self.time, now, tz)
        return alert_time

    def get_occurences(self, begin=None, days=30):
        """Get some dates in this series of reminders. Returns a list of datetime objects"""
        if self.disabled:
            return []

        tz = self.get_tz()
        if begin is None:
            begin = self.get_alert_time(tz)  # "today's" alert time.
        end = begin + timedelta(days=days)  # alerts a month in the future
        dates = list(self.recurrences.occurrences(
            dtstart=begin,
            dtend=end
        ))

        # Since the dtstart argument to `occurences` means that we _always_
        # include that date in the list, we now need to filter out any dates
        # that shouldn't occur on given days. This is a dirty hack.
        def _filter_days(d):
            recurrences_text = self.recurrences_as_text().lower()
            dow = d.strftime("%A").lower()
            if recurrences_text.startswith("weekly") and dow not in recurrences_text:
                return False
            return True
        dates = list(filter(_filter_days, dates))

        # IF our recurrences are empty, just keep the first date.
        if self.recurrences_as_text() == '':
            dates = dates[0:1]

        # Return only dates matching "today" or later.
        now = timezone.now().astimezone(tz)
        return list(filter(lambda d: d.date() >= now.date(), dates))

    def _stopped_by_completion(self, user=None):
        """Determine if triggers should stop because the user has completed
        the action associated with this trigger. This is messy, but it:

        - users the given user, falling back to self.user
        - returns False for no user
        - if this is a default trigger, it looks up the UserCompletedAction
          for the Action on which it is defined as a default
        - if this is a custom trigger, it looks up the UserCompletedAction
          for the associated UserAction
        - If it finds a UserCompletedAction with a state of "complete" it
          returns True
        - If it fails any of the above, it returns False

        Returns True if the trigger should stop, False otherwise.
        """
        from .progress import UserCompletedAction
        user = user or self.user
        if user and self.stop_on_complete:  # This only works if we have a user
            try:
                # While it's technically possible that this trigger could be
                # associated with more than one UserAction, it's unlikely,
                ua = user.useraction_set.filter(custom_trigger=self).first()
                if ua is None:  # This may be a default trigger...
                    ua = user.useraction_set.filter(action=self.action_default).first()
                if ua:
                    # Try to get the UserAction associated with the trigger
                    params = {
                        'user': user,
                        'useraction': ua,
                        'action': ua.action,
                        'state': UserCompletedAction.COMPLETED,
                    }
                    return UserCompletedAction.objects.filter(**params).exists()
            except ObjectDoesNotExist:
                pass
        return False

    def next(self, user=None):
        """Generate the next date for this Trigger. For recurring triggers,
        this will return a datetime object for the next time the trigger should
        fire in the user's local time if, this object is associated with a
        user; otherwise, the date will be in UTC.

        """
        if self._stopped_by_completion(user) or self.disabled:
            return None

        if self.is_dynamic:
            return self.dynamic_trigger_date(user=user)

        tz = self.get_tz(user=user)
        alert_on = self.get_alert_time(tz)
        now = timezone.now().astimezone(tz)
        recurrences = self.serialized_recurrences()

        # No recurrences, alert is in the future
        if recurrences is None and alert_on and alert_on > now:
            return alert_on

        # HACK: If we've stacked a number of RRULEs, let's generate a list of
        # dates in the recurrence (30 days out & starting with the current
        # time), then pick the earliest one.
        elif recurrences and "\n" in recurrences:
            # Generate some dates, keeping only the future ones
            dates = [dt for dt in self.get_occurences(begin=now) if dt > now]
            # Then recombine them all with the trigger time. ugh. :(
            dates = [self._combine(self.time, date) for date in dates]
            if len(dates) > 0:
                return dates[0]

        # HACK to make sure the UNTIL recurrences don't sometime keep returning
        # dates after their specified ending (but don't clobber rules that
        # specify a weekly recurrence for set days; these need to use
        # `recurrences.after`
        elif recurrences and "UNTIL" in recurrences and 'BYDAY' not in recurrences:
            yesterday = alert_on - timedelta(days=1)  # yesterday's alert
            tomorrow = now + timedelta(days=1)  # this time tomorrow
            dates = self.recurrences.between(now, tomorrow, dtstart=yesterday)
            if len(dates) > 0:
                return dates[0]
            else:
                return None

        # Return the next value in the recurrence
        elif recurrences and alert_on:
            return self.recurrences.after(
                now,  # The next recurrence after the current time.
                inc=True,  # return the current time if it matches the recurrence.
                dtstart=alert_on  # The alert time.
            )

        # No recurrence or not a time-pased Trigger.
        return None

    def previous(self, user=None, lookback=30):
        """If this trigger is for a recurring event, this method will generate
        the previous instance of the recurrence in the user's timezone;
        otherwise it will return None.

        Returns the time in the user's local timezone (or None)

        """
        user = self.user or user
        if user is None:
            raise AssertionError("Trigger.previous requires a user.")

        if user and self.recurrences is not None and self.time:
            # recurrences only work with naive datetimes,
            # so try to get today's start
            today = local_day_range(user)[0]
            today = today.replace(tzinfo=None)
            start = today - timedelta(days=lookback)

            dates = self.recurrences.between(
                after=start,
                before=today,
                dtstart=start,
            )
            if len(dates):
                dt = max(dates)
                dt = datetime.combine(dt, self.time.replace(tzinfo=None))
                dt = to_localtime(dt, user)
                return dt
        return None

    objects = TriggerManager()
