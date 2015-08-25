"""Models for the Goals app.

This is our collection of Goals & Behaviors. They're organized as follows:

    [Category] <-> [Goal] <-> [Behavior] <- [Action]

Actions are the things we want to help people to do.

"""
import os
import pytz

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models, IntegrityError
from django.db.models import Avg
from django.db.models.signals import (
    pre_delete, pre_save, post_delete, post_save
)
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils import timezone

from django_fsm import FSMField, transition
from markdown import markdown
from recurrence import serialize as serialize_recurrences
from recurrence.fields import RecurrenceField
from utils import colors, dateutils

from .managers import (
    CategoryManager,
    PackageEnrollmentManager,
    TriggerManager,
    UserActionManager,
    WorkflowManager
)
from .mixins import ModifiedMixin, StateMixin, UniqueTitleMixin, URLMixin
from .utils import clean_title, clean_notification, strip


class Category(ModifiedMixin, StateMixin, UniqueTitleMixin, URLMixin, models.Model):
    """A Broad grouping of possible Goals from which users can choose.

    We also have content (goals, behaviors, actions) that is associated with
    a single organization. We've been referring to this scenario as "packaged
    content", and in this case a Category serves as the Organization's content
    "container".

    """

    # URLMixin attributes
    urls_app_namespace = "goals"
    urls_model_name = "category"
    urls_icon_field = "icon"
    urls_image_field = "image"

    # Data Fields
    packaged_content = models.BooleanField(
        default=False,
        help_text="Is this Category for a collection of packaged content?"
    )
    package_contributors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        help_text="The group of users that will contribute to content in "
                  "this category."
    )
    order = models.PositiveIntegerField(
        unique=True,
        help_text="Controls the order in which Categories are displayed."
    )
    title = models.CharField(
        max_length=128,
        db_index=True,
        unique=True,
        help_text="A Title for the Category (50 characters)"
    )
    title_slug = models.SlugField(max_length=128, db_index=True, unique=True)
    description = models.TextField(
        help_text="A short (250 character) description for this Category"
    )
    icon = models.ImageField(
        upload_to="goals/category", null=True, blank=True,
        help_text="Upload a square icon to be displayed for the Category."
    )
    image = models.ImageField(
        upload_to="goals/category/images",
        null=True,
        blank=True,
        help_text="A Hero image to be displayed at the top of the Category pager"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes regarding this Category"
    )
    color = models.CharField(
        max_length=7,
        default="#2ECC71",
        help_text="Select the color for this Category"
    )
    secondary_color = models.CharField(
        max_length=7,
        blank=True,
        help_text="Select a secondary color for this Category. If omitted, a "
                  "complementary color will be generated."
    )
    state = FSMField(default="draft")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="categories_updated",
        null=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="categories_created",
        null=True
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order', 'title']
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        # add_category, change_category, delete_category are created by default.
        permissions = (
            ("view_category", "Can view Categories"),
            ("decline_category", "Can Decline Categories"),
            ("publish_category", "Can Publish Categories"),
        )

    @property
    def is_packaged(self):
        return self.packaged_content

    @property
    def rendered_description(self):
        """Render the description markdown"""
        return markdown(self.description)

    @property
    def goals(self):
        """This property returns a QuerySet of the related Goal objects."""
        return self.goal_set.all().distinct()

    @property
    def behaviors(self):
        """Returns a QuerySet of all Behaviors nested beneath this category's
        set of goals."""
        ids = self.goals.values_list('behavior', flat=True)
        return Behavior.objects.filter(pk__in=ids)

    def _format_color(self, color):
        """Ensure that colors include a # symbol at the beginning."""
        return color if color.startswith("#") else "#{0}".format(color)

    def _generate_secondary_color(self):
        if self.secondary_color:
            return self.secondary_color
        else:
            return colors.lighten(self.color)

    def save(self, *args, **kwargs):
        """Always slugify the name prior to saving the model and set
        created_by or updated_by fields if specified."""
        self.title_slug = slugify(self.title)
        self.color = self._format_color(self.color)
        self.secondary_color = self._generate_secondary_color()
        kwargs = self._check_updated_or_created_by(**kwargs)
        super(Category, self).save(*args, **kwargs)

    @transition(field=state, source="*", target='draft')
    def draft(self):
        pass

    @transition(field=state, source=["draft", "declined"], target='pending-review')
    def review(self):
        pass

    @transition(field=state, source="pending-review", target='declined')
    def decline(self):
        pass

    @transition(field=state, source=["draft", "pending-review"], target='published')
    def publish(self):
        pass

    def get_view_enrollment_url(self):
        """Essentially a Detail view for a Category Package."""
        return reverse("goals:package-detail", args=[self.id])

    def get_enroll_url(self):
        return reverse("goals:package-enroll", args=[self.id])

    objects = CategoryManager()


class Goal(ModifiedMixin, StateMixin, UniqueTitleMixin, URLMixin, models.Model):

    # URLMixin attributes
    urls_app_namespace = "goals"
    urls_model_name = "goal"
    urls_icon_field = "icon"

    # Data Fields
    categories = models.ManyToManyField(
        Category,
        blank=True,
        help_text="Select the Categories in which this Goal should appear."
    )
    title_slug = models.SlugField(max_length=256, null=True)
    title = models.CharField(
        max_length=256, db_index=True, unique=True,
        help_text="A Title for the Goal (50 characters)"
    )
    subtitle = models.CharField(
        max_length=256,
        null=True,
        help_text="A one-liner description for this goal."
    )
    description = models.TextField(
        blank=True,
        help_text="A short (250 character) description for this Goal"
    )
    outcome = models.TextField(
        blank=True,
        help_text="Desired outcome of this Goal."
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Misc notes about this item. This is for your use and will "
                  "not be displayed in the app."
    )
    more_info = models.TextField(
        blank=True,
        help_text="Optional tips and tricks or other small, associated ideas. "
                  "Consider using bullets."
    )
    icon = models.ImageField(
        upload_to="goals/goal", null=True, blank=True,
        help_text="Upload an icon (256x256) for this goal"
    )
    state = FSMField(default="draft")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="goals_updated",
        null=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="goals_created",
        null=True
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{0}".format(self.title)

    class Meta:
        ordering = ['title']
        verbose_name = "Goal"
        verbose_name_plural = "Goals"
        # add_goal, change_goal, delete_goal are created by default.
        permissions = (
            ("view_goal", "Can view Goals"),
            ("decline_goal", "Can Decline Goals"),
            ("publish_goal", "Can Publish Goals"),
        )

    @property
    def rendered_description(self):
        """Render the description markdown"""
        return markdown(self.description)

    def save(self, *args, **kwargs):
        """Always slugify the title prior to saving the model."""
        self.title_slug = slugify(self.title)
        kwargs = self._check_updated_or_created_by(**kwargs)
        super(Goal, self).save(*args, **kwargs)

    @transition(field=state, source="*", target='draft')
    def draft(self):
        pass

    @transition(field=state, source=["draft", "declined"], target='pending-review')
    def review(self):
        pass

    @transition(field=state, source="pending-review", target='declined')
    def decline(self):
        pass

    @transition(field=state, source=["draft", "pending-review"], target='published')
    def publish(self):
        pass

    objects = WorkflowManager()


class Trigger(URLMixin, models.Model):
    """This class encapsulates date (and in the future, location) -based triggers
    for Behaviors and Actions.

    For date or time-based items, a Trigger consists of:

    1. A time (optional); When during the day should the notification be sent.
    2. Recurrences: How frequently (every day, once a month, etc) should the
       notification be sent.

    This model is heavily based on django-recurrence:
    https://django-recurrence.readthedocs.org

    """
    # URLMixin attributes
    urls_app_namespace = "goals"
    urls_model_name = "trigger"
    urls_slug_field = "name_slug"

    # Data Fields
    TRIGGER_TYPES = (
        ('time', 'Time'),
        ('place', 'Place'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        help_text="A Custom trigger, created by a user."
    )
    name = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
        help_text="Give this trigger a helpful name. It must be unique, and "
                  "will be used in drop-down lists and other places where you"
                  "can select it later."
    )
    name_slug = models.SlugField(max_length=128, db_index=True, unique=True)
    trigger_type = models.CharField(
        max_length=10,
        choices=TRIGGER_TYPES,
        default="time",
        help_text='The type of Trigger used, e.g. a time-based trigger'
    )
    location = models.CharField(
        max_length=256,
        blank=True,
        help_text="Only used when Trigger type is location. "
                  "Can be 'home', 'work', or a (lat, long) pair."
    )
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

    def __str__(self):
        df = "%Y-%m-%d"
        d = '' if self.trigger_date is None else self.trigger_date.strftime(df)
        t = '' if self.time is None else self.time.strftime("%H:%M")
        r = self.recurrences_as_text()
        return "{0} {1} {2} {3}".format(self.name, d, t, r)

    class Meta:
        verbose_name = "Trigger"
        verbose_name_plural = "Triggers"
        permissions = (
            ("view_trigger", "Can view Triggers"),
            ("decline_trigger", "Can Decline Triggers"),
            ("publish_trigger", "Can Publish Triggers"),
        )

    @property
    def is_time_trigger(self):
        return self.trigger_type == "time"

    @property
    def is_place_trigger(self):
        return self.trigger_type == "place"

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

    def save(self, *args, **kwargs):
        """Always slugify the name prior to saving the model."""
        self.name_slug = slugify(self.name)
        self._localize_time()
        self._strip_rdate_data()
        super(Trigger, self).save(*args, **kwargs)

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
        dt = datetime.combine(a_date, a_time)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone=tz)
        elif timezone.is_aware(dt) and tz is not None:
            dt = dt.astimezone(tz)

        return dt

    def get_tz(self):
        """Return a Timezone object for the user; defaults to UTC if no user."""
        if self.user:
            return pytz.timezone(self.user.userprofile.timezone)
        return timezone.utc

    def get_alert_time(self, tz=None):
        """Return a datetime object (with appropriate timezone) for the
        starting date/time for this trigger."""
        if tz is None:
            tz = self.get_tz()
        alert_time = None
        if self.trigger_date and self.time:
            alert_time = self._combine(self.time, self.trigger_date, tz)
        elif self.time:
            now = timezone.now().astimezone(tz)
            alert_time = self._combine(self.time, now, tz)
        return alert_time

    def get_occurences(self, begin=None, days=30):
        """Get some dates in this series of reminders."""
        tz = self.get_tz()
        if begin is None:
            begin = self.get_alert_time(tz)  # "today's" alert time.
        end = begin + timedelta(days=30)  # alerts a month in the future
        dates = list(self.recurrences.occurrences(
            dtstart=begin,
            dtend=end
        ))

        # Return only dates in the future.
        now = timezone.now().astimezone(tz)
        return list(filter(lambda d: d > now, dates))

    def next(self):
        """Generate the next date for this Trigger. For recurring triggers,
        this will return a datetime object for the next time the trigger should
        fire in the user's local time if, this object is associated with a
        user; otherwise, the date will be in UTC.

        """
        tz = self.get_tz()
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
            dates = self.get_occurences(begin=now)  # Generate some dates.
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
        elif recurrences:
            return self.recurrences.after(
                now,  # The next recurrence after the current time.
                inc=True,  # return the current time if it matches the recurrence.
                dtstart=alert_on  # The alert time.
            )

        # No recurrence or not a time-pased Trigger.
        return None

    def formatted_next(self):
        n = self.next()
        if n is not None:
            return n.strftime("%c")
        return "N/A"

    objects = TriggerManager()


def _behavior_icon_path(instance, filename):
    """Return the path for uploaded icons for `Behavior` and `Action` objects."""
    p = "goals/{0}/icons".format(type(instance).__name__.lower())
    return os.path.join(p, filename)


def _behavior_img_path(instance, filename):
    """Return the path for uploaded images for `Behavior` and `Action` objects."""
    p = "goals/{0}/images".format(type(instance).__name__.lower())
    return os.path.join(p, filename)


class BaseBehavior(ModifiedMixin, StateMixin, models.Model):
    """This abstract base class contains fields that are common to both
    `Behavior` and `Action` models.

    """
    source_link = models.URLField(
        max_length=256,
        blank=True,
        null=True,
        help_text="A link to the source."
    )
    source_notes = models.TextField(
        blank=True,
        help_text="Narrative notes about the source of this item."
    )
    notes = models.TextField(
        blank=True,
        help_text="Misc notes about this item. This is for your use and will "
                  "not be displayed in the app."
    )
    more_info = models.TextField(
        blank=True,
        help_text="Optional tips and tricks or other small, associated ideas. "
                  "Consider using bullets."
    )
    description = models.TextField(
        blank=True,
        help_text="A brief (250 characters) description about this item."
    )
    case = models.TextField(
        blank=True,
        help_text="Brief description of why this is useful."
    )
    outcome = models.TextField(
        blank=True,
        help_text="Brief description of what the user can expect to get by "
                  "adopting the behavior"
    )
    external_resource = models.CharField(
        blank=True,
        max_length=256,
        help_text=("An external resource is something that will help a user "
                   "accomplish a task. It could be a phone number, link to a "
                   "website, link to another app, or GPS coordinates. ")
    )
    external_resource_name = models.CharField(
        blank=True,
        max_length=256,
        help_text=("A human-friendly name for your external resource. This is "
                   "especially helpful for web links.")
    )
    notification_text = models.CharField(
        max_length=256,
        blank=True,
        help_text="Text of the notification (50 characters)"
    )
    icon = models.ImageField(
        upload_to=_behavior_icon_path,
        null=True,
        blank=True,
        help_text="A square icon for this item in the app, preferrably 512x512."
    )
    image = models.ImageField(
        upload_to=_behavior_img_path,
        null=True,
        blank=True,
        help_text="An image to be displayed for this item, preferrably 1024x1024."
    )
    state = FSMField(default="draft")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return "{0}".format(self.title)

    def _set_notification_text(self):
        if not self.notification_text:
            self.notification_text = self.title

    @property
    def rendered_description(self):
        """Render the description markdown"""
        return markdown(self.description)

    @property
    def rendered_more_info(self):
        """Render the more_info markdown"""
        return markdown(self.more_info)

    def save(self, *args, **kwargs):
        """Always slugify the name prior to saving the model."""
        self.title_slug = slugify(self.title)
        kwargs = self._check_updated_or_created_by(**kwargs)
        self._set_notification_text()
        super(BaseBehavior, self).save(*args, **kwargs)

    @transition(field=state, source="*", target='draft')
    def draft(self):
        pass

    @transition(field=state, source=["draft", "declined"], target='pending-review')
    def review(self):
        pass

    @transition(field=state, source="pending-review", target='declined')
    def decline(self):
        pass

    @transition(field=state, source=["draft", "pending-review"], target='published')
    def publish(self):
        pass


class Behavior(URLMixin, UniqueTitleMixin,  BaseBehavior):
    """A Behavior. Behaviors have many actions associated with them and contain
    several bits of information for a user."""

    # URLMixin attributes
    urls_app_namespace = "goals"
    urls_model_name = "behavior"
    urls_icon_field = "icon"
    urls_image_field = "image"

    # Data Fields
    title = models.CharField(
        max_length=256,
        db_index=True,
        unique=True,
        help_text="A unique title for this Behavior (50 characters)"
    )
    title_slug = models.SlugField(max_length=256, db_index=True, unique=True)
    goals = models.ManyToManyField(
        Goal,
        blank=True,
        help_text="Select the Goal(s) that this Behavior achieves."
    )
    informal_list = models.TextField(
        blank=True,
        help_text="Use this section to create a list of specific actions for "
                  "this behavior. This list will be reproduced as a mnemonic "
                  "on the Action entry page"
    )
    default_trigger = models.ForeignKey(
        Trigger,
        blank=True,
        null=True,
        help_text="A trigger/reminder for this behavior"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="behaviors_updated",
        null=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="behaviors_created",
        null=True
    )

    class Meta(BaseBehavior.Meta):
        ordering = ['title']
        verbose_name = "Behavior"
        verbose_name_plural = "Behaviors"
        # add_behavior, change_behavior, delete_behavior are created by default.
        permissions = (
            ("view_behavior", "Can view Permissions"),
            ("decline_behavior", "Can Decline Permissions"),
            ("publish_behavior", "Can Publish Permissions"),
        )

    @property
    def categories(self):
        """Return a QuerySet of Categories for this object's selected Goals"""
        cats = self.goals.values_list('categories', flat=True)
        return Category.objects.filter(pk__in=cats)

    def get_user_mapping(self, user):
        """Return the first UserBehavior object that matches this Behavior and
        the given user. There _should_ only be one of these. Returns None if
        the object is not found.

        Note: This method can be used by other apps that may have a generic
        relationships (e.g. notifications).

        """
        return self.userbehavior_set.filter(user=user, behavior=self).first()

    objects = WorkflowManager()


class Action(URLMixin, BaseBehavior):
    """Actions are things that people do, and are typically the bit of
    information to which a user will set a reminder (e.g. a Trigger).

    Actions can be of different types, i.e.:

    * Starter Step
    * Tiny Version
    * Resource
    * Right now
    * Custom

    """
    STARTER = "starter"
    TINY = "tiny"
    RESOURCE = "resource"
    NOW = "now"
    LATER = "later"
    CUSTOM = "custom"

    ACTION_TYPE_CHOICES = (
        (STARTER, 'Starter Step'),
        (TINY, 'Tiny Version'),
        (RESOURCE, 'Resource'),
        (NOW, 'Do it now'),
        (LATER, 'Do it later'),
        (CUSTOM, 'Custom'),
    )

    # URLMixin attributes
    urls_fields = ['pk', 'title_slug']
    urls_app_namespace = "goals"
    urls_model_name = "action"
    urls_icon_field = "icon"
    urls_image_field = "image"
    default_icon = "img/compass-grey.png"
    notification_title = "Time for me to..."

    # Data Fields
    title = models.CharField(
        max_length=256,
        db_index=True,
        help_text="A short (50 character) title for this Action"
    )
    title_slug = models.SlugField(max_length=256, db_index=True)

    behavior = models.ForeignKey(Behavior, verbose_name="behavior")
    action_type = models.CharField(
        max_length=32,
        default=CUSTOM,
        choices=ACTION_TYPE_CHOICES,
        db_index=True,
    )
    sequence_order = models.IntegerField(
        default=0,
        db_index=True,
        help_text="Order/number of action in stepwise sequence of behaviors"
    )
    default_trigger = models.OneToOneField(
        Trigger,
        blank=True,
        null=True,
        help_text="A trigger/reminder for this behavior",
        related_name="action_default"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="actions_updated",
        null=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="actions_created",
        null=True
    )

    @classmethod
    def get_create_starter_action_url(cls):
        return "{0}?actiontype={1}".format(
            reverse("goals:action-create"), cls.STARTER)

    @classmethod
    def get_create_tiny_action_url(cls):
        return "{0}?actiontype={1}".format(
            reverse("goals:action-create"), cls.TINY)

    @classmethod
    def get_create_resource_action_url(cls):
        return "{0}?actiontype={1}".format(
            reverse("goals:action-create"), cls.RESOURCE)

    @classmethod
    def get_create_now_action_url(cls):
        return "{0}?actiontype={1}".format(
            reverse("goals:action-create"), cls.NOW)

    @classmethod
    def get_create_later_action_url(cls):
        return "{0}?actiontype={1}".format(
            reverse("goals:action-create"), cls.LATER)

    @classmethod
    def get_create_custom_action_url(cls):
        return "{0}?actiontype={1}".format(
            reverse("goals:action-create"), cls.CUSTOM)

    class Meta(BaseBehavior.Meta):
        ordering = ['sequence_order', 'title']
        verbose_name = "Action"
        verbose_name_plural = "Actions"
        # add_action, change_action, delete_action are created by default.
        permissions = (
            ("view_action", "Can view Actions"),
            ("decline_action", "Can Decline Actions"),
            ("publish_action", "Can Publish Actions"),
        )

    def get_user_mapping(self, user):
        """Return the first UserAction object that matches this Action and the
        given user. There _should_ only be one of these. Returns None if the
        object is not found.

        Note: This method can be used by other apps that may have a generic
        relationships (e.g. notifications).

        """
        return self.useraction_set.filter(user=user, action=self).first()

    objects = WorkflowManager()


# ----------------------------------
# Signals for public content models.
# ----------------------------------
@receiver(pre_save, sender=Action)
@receiver(pre_save, sender=Behavior)
@receiver(pre_save, sender=Goal)
@receiver(pre_save, sender=Category)
def clean_content(sender, instance, raw, using, **kwargs):
    # A mapping of model field names and the function that cleans them.
    clean_functions = {
        "title": clean_title,
        "subtitle": clean_title,
        "description": strip,
        "more_info": strip,
        "notification_text": clean_notification,
    }
    for field, func in clean_functions.items():
        if hasattr(instance, field):
            setattr(instance, field, func(getattr(instance, field)))


@receiver(post_delete, sender=Action)
@receiver(post_delete, sender=Behavior)
@receiver(post_delete, sender=Goal)
@receiver(post_delete, sender=Category)
def delete_model_icon(sender, instance, using, **kwargs):
    """Once a model instance has been deleted, this will remove its `icon` from
    the filesystem."""
    if hasattr(instance, 'icon') and instance.icon:
        instance.icon.delete()


@receiver(post_delete, sender=Action)
@receiver(post_delete, sender=Behavior)
def delete_model_image(sender, instance, using, **kwargs):
    """Once a model instance has been deleted, this will remove its `image`
    from the filesystem."""
    if hasattr(instance, 'image') and instance.image:
        instance.image.delete()


# -----------------------------------------------------------------------------
#
# Models that track a user's progress toward Goals, Behaviors, Actions.
#
# -----------------------------------------------------------------------------
class UserGoal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    goal = models.ForeignKey(Goal)
    completed = models.BooleanField(default=False)
    completed_on = models.DateTimeField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{0}".format(self.goal.title)

    class Meta:
        ordering = ['user', 'goal']
        unique_together = ("user", "goal")
        verbose_name = "User Goal"
        verbose_name_plural = "User Goals"

    def get_user_behaviors(self):
        """Returns a QuerySet of Behaviors related to this Goal, but restricts
        those behaviors to those which the user has selected.

        """
        bids = self.user.userbehavior_set.values_list('behavior_id', flat=True)
        return self.goal.behavior_set.filter(id__in=bids)

    def get_user_categories(self):
        """Returns a QuerySet of Categories related to this Goal, but restricts
        those categories to those which the user has selected.

        NOTE: This method also looks up the user's `CategoryProgress` for
        each category, and appends a `progress_value` attribute.
        """
        cids = self.user.usercategory_set.values_list('category__id', flat=True)

        # Find all the lastest CategoryProgress objects for each user/category
        scores = {}
        for cid in cids:
            try:
                scores[cid] = CategoryProgress.objects.filter(
                    user=self.user,
                    category__id=cid
                ).latest().current_score
            except CategoryProgress.DoesNotExist:
                scores[cid] = 0.0

        results = self.goal.categories.filter(id__in=cids)
        for category in results:
            category.progress_value = scores.get(category.id, 0.0)
        return results

    @property
    def progress_value(self):
        try:
            qs = self.goal.goalprogress_set.filter(user=self.user)
            return qs.latest().current_score
        except GoalProgress.DoesNotExist:
            return 0.0


@receiver(pre_delete, sender=UserGoal, dispatch_uid="del_goal_behaviors")
def delete_goal_child_behaviors(sender, instance, using, **kwargs):
    """If a user is removing a goal, delete all of the user's selected
    behaviors that have *no other* parent goal."""
    # Get a list of all goals selected by the user, excluding the one
    # we're about to remove.
    user_goals = UserGoal.objects.filter(user=instance.user)
    user_goals = user_goals.exclude(id=instance.id)
    user_goals = user_goals.values_list('goal', flat=True)

    # Delete all the user's behaviors that lie ONLY in the goal we're
    # about to remove
    user_behaviors = instance.user.userbehavior_set.all()
    user_behaviors = user_behaviors.exclude(behavior__goals__in=user_goals)
    user_behaviors.delete()


class UserBehavior(models.Model):
    """A Mapping between Users and the Behaviors they've selected.

    NOTE: notifications for this are scheduled by the `create_notifications`
    management command.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    behavior = models.ForeignKey(Behavior)
    custom_trigger = models.ForeignKey(
        Trigger,
        blank=True,
        null=True,
        help_text="A User-defined trigger for this behavior"
    )
    completed = models.BooleanField(default=False)
    completed_on = models.DateTimeField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{0}".format(self.behavior.title)

    class Meta:
        ordering = ['user', 'behavior']
        unique_together = ("user", "behavior")
        verbose_name = "User Behavior"
        verbose_name_plural = "User Behaviors"

    def get_user_categories(self):
        """Returns a QuerySet of Categories related to this Behavior, but
        restricts the result to those Categories which the user has selected."""
        # User-selected categories
        a = set(self.user.usercategory_set.values_list('category__id', flat=True))
        # Parent categories (through goals)
        b = set(self.behavior.goals.values_list("categories", flat=True))
        # The overlap
        ids = a.intersection(b)
        return Category.objects.filter(id__in=ids)

    def get_user_goals(self):
        """Returns a QuerySet of Goals related to this Behavior, but restricts
        those goals to those which the user has selected."""
        gids = self.user.usergoal_set.values_list('goal__id', flat=True)
        return self.behavior.goals.filter(id__in=gids)

    def get_custom_trigger_name(self):
        """This should generate a unique name for this object's custom
        trigger."""
        return "custom trigger for userbehavior-{0}".format(self.id)

    def get_user_actions(self):
        """Returns a QuerySet of Actions related to this Behavior, but
        restricts the results to those which the user has selected.

        """
        uids = self.user.useraction_set.values_list('action_id', flat=True)
        return self.behavior.action_set.filter(id__in=uids)


@receiver(pre_delete, sender=UserBehavior, dispatch_uid="del_behavior_actions")
def delete_behavior_child_actions(sender, instance, using, **kwargs):
    """If a user is removing a behavior, delete all of the user's selected
    actions that are a child of this behavior."""

    user_actions = instance.user.useraction_set.filter(
        action__behavior=instance.behavior
    )
    user_actions.delete()


@receiver(post_delete, sender=UserBehavior)
def remove_behavior_reminders(sender, instance, using, **kwargs):
    """If a user deletes ALL of their UserBehavior instances, we should also
    remove the currently-queued GCMMessage for the Behavior/Priority reminder.

    """
    # NOTE: All behavior reminders use the default trigger, and we're not
    # actually connecting them to any content types, so that's null.

    if not UserBehavior.objects.filter(user=instance.user).exists():
        try:
            from notifications.models import GCMMessage
            from notifications.settings import DEFAULTS
            messages = GCMMessage.objects.filter(
                user=instance.user,
                content_type=None,
                title=DEFAULTS['DEFAULT_TITLE']
            )
            messages.delete()
        except (ImportError, ContentType.DoesNotExist):
            pass


class UserAction(models.Model):
    """A Mapping between Users and the Actions they've selected.

    NOTE: notifications for this are scheduled by the `create_notifications`
    management command.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    action = models.ForeignKey(Action)
    custom_trigger = models.ForeignKey(
        Trigger,
        blank=True,
        null=True,
        help_text="A User-defined trigger for this behavior"
    )
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{0}".format(self.action.title)

    class Meta:
        ordering = ['user', 'action']
        unique_together = ("user", "action")
        verbose_name = "User Action"
        verbose_name_plural = "User Actions"

    @property
    def default_trigger(self):
        return self.action.default_trigger

    def get_custom_trigger_name(self):
        """This should generate a unique name for this object's custom
        trigger."""
        return "custom trigger for useraction-{0}".format(self.id)

    objects = UserActionManager()


@receiver(post_delete, sender=UserAction)
def remove_action_reminders(sender, instance, using, **kwargs):
    """If a user deletes one of their UserAction instances, we should also
    remove the GCMMessage associated with it, so they don't get a
    notification.

    NOTE: GCMMessages have a generic relationship to the Action
    """
    # Remove any custom triggers associated with this object.
    try:
        if instance.custom_trigger:
            instance.custom_trigger.delete()
    except Trigger.DoesNotExist:
        # This really shouldn't happen, but sometimes it does when cleaning
        # up generated objects in our test suite
        pass

    try:
        # Remove any pending notifications
        from notifications.models import GCMMessage
        action_type = ContentType.objects.get_for_model(Action)
        messages = GCMMessage.objects.filter(
            content_type=action_type,
            object_id=instance.action.id,
            user=instance.user
        )
        messages.delete()
    except (ImportError, ContentType.DoesNotExist):
        pass


class UserCompletedAction(models.Model):
    """Users can tell us they "completed" an Action. This is represented in
    the mobile app by a 'I did it' button.

    Note that there may be many instances of this model for a user/action, and
    that an aggregate of these tells us how often a user performs (or says they
    perform) this action.

    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    useraction = models.ForeignKey(UserAction)
    action = models.ForeignKey(Action)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{0}".format(self.action.title)

    class Meta:
        ordering = ['user', 'action']
        verbose_name = "User Completed Action"
        verbose_name_plural = "User Completed Action"


class UserCategory(models.Model):
    """A Mapping between users and specific categories."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    category = models.ForeignKey(Category)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{0}".format(self.category.title)

    class Meta:
        ordering = ['user', 'category']
        unique_together = ("user", "category")
        verbose_name = "User Category"
        verbose_name_plural = "User Categories"

    def get_user_goals(self):
        """Returns a QuerySet of Goals related to this Category, but restricts
        those goals to those which the user has selected."""
        gids = self.user.usergoal_set.values_list('goal__id', flat=True)
        return self.category.goals.filter(id__in=gids)

    @property
    def progress_value(self):
        try:
            qs = self.category.categoryprogress_set.filter(user=self.user)
            return qs.latest().current_score
        except CategoryProgress.DoesNotExist:
            return 0.0


@receiver(pre_delete, sender=UserCategory, dispatch_uid="del_cat_goals")
def delete_category_child_goals(sender, instance, using, **kwargs):
    """If a user is removing a category, delete all of the user's selected
    goals that have *no other* parent category."""
    # Get a list of all categories selected by the user, excluding the one
    # we're about to remove.
    user_categories = UserCategory.objects.filter(user=instance.user)
    user_categories = user_categories.exclude(id=instance.id)
    user_categories = user_categories.values_list('category', flat=True)

    # Delete all the user's goals that lie ONLY in the category we're
    # about to remove
    user_goals = instance.user.usergoal_set.all()
    user_goals = user_goals.exclude(goal__categories__in=user_categories)
    user_goals.delete()


class BehaviorProgress(models.Model):
    """Encapsulates a user's progress & history toward certain behaviors."""
    OFF_COURSE = 1
    SEEKING = 2
    ON_COURSE = 3

    PROGRESS_CHOICES = (
        (OFF_COURSE, "Off Course"),
        (SEEKING, "Seeking"),
        (ON_COURSE, "On Course"),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    user_behavior = models.ForeignKey(UserBehavior)
    status = models.IntegerField(choices=PROGRESS_CHOICES)
    reported_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reported_on']
        get_latest_by = "reported_on"
        verbose_name = "Behavior Progress"
        verbose_name_plural = "Behavior Progression"

    def __str__(self):
        return self.get_status_display()

    @property
    def status_display(self):
        return self.get_status_display()

    @property
    def behavior(self):
        return self.user_behavior.behavior


@receiver(post_save, sender=BehaviorProgress, dispatch_uid="recalc_goal_progress")
def recalculate_goal_progress(sender, instance, created, **kwargs):
    """This signal handler will re-calculate the most recent GoalProgress
    instance when a BehaviorProgress is created."""
    if created:
        # Get all possible goal ids associated with the user
        for gid in instance.user_behavior.behavior.goals.values_list("id", flat=True):
            try:
                # Recalculate the score from all related BehaviorProgress objects
                gp = GoalProgress.objects.filter(user=instance.user, goal__id=gid).latest()
                gp.recalculate_score()
                gp.save()
            except GoalProgress.DoesNotExist:
                pass


class GoalProgressManager(models.Manager):
    """Custom manager for the `GoalProgress` class that includes a method
    to generate scores for a User's progress toward a Goal.

    NOTE: This is defined here (in models.py) instead of in managers.py, so
    we have access to the Goal & BehaviorProgress models.

    """

    def _get_or_update(self, user, goal, scores, current_time):
        # check to see if we've already got a GoalProgress object for this date
        start, end = dateutils.date_range(current_time)

        # do the aggregation
        score_total = sum(scores)
        score_max = len(scores) * BehaviorProgress.ON_COURSE

        try:
            gp = self.filter(
                user=user,
                goal=goal,
                reported_on__range=(start, end)
            ).latest()
            gp.current_total = score_total
            gp.max_total = score_max
            gp.save()
        except self.model.DoesNotExist:
            gp = self.create(
                user=user,
                goal=goal,
                current_total=score_total,
                max_total=score_max
            )
        return gp

    def generate_scores(self, user):
        created_objects = []
        current_time = timezone.now()

        # Get all the goals that a user has selected IFF that user has also
        # selected some Behaviors.
        #
        # This is the intersection of:
        # - the set of goal ids that contain behavior's i've selected
        # - the set of goals i've selected
        ubgs = UserBehavior.objects.filter(user=user)
        ubgs = set(ubgs.values_list('behavior__goals__id', flat=True))

        goal_ids = UserGoal.objects.filter(user=user)
        goal_ids = set(goal_ids.values_list('goal', flat=True))
        goal_ids = goal_ids.intersection(ubgs)

        for goal in Goal.objects.filter(id__in=goal_ids):
            # Get all the User's selected behavior (ids) within that goal.
            behaviors = UserBehavior.objects.filter(
                user=user,
                behavior__goals=goal
            ).values_list('behavior', flat=True)

            if behaviors.exists():
                # All the self-reported scores up to this date for this goal
                scores = BehaviorProgress.objects.filter(
                    user_behavior__behavior__id__in=behaviors,
                    user=user,
                    reported_on__lte=current_time
                ).values_list('status', flat=True)

                # Create a GoalProgress object for this data
                gp = self._get_or_update(user, goal, scores, current_time)
                created_objects.append(gp.id)
        return self.get_queryset().filter(id__in=created_objects)


class GoalProgress(models.Model):
    """Agregates data from `BehaviorProgression` up to 'today'."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    goal = models.ForeignKey(Goal)
    current_score = models.FloatField()
    current_total = models.FloatField()
    max_total = models.FloatField()
    reported_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reported_on']
        get_latest_by = "reported_on"
        verbose_name = "Goal Progress"
        verbose_name_plural = "Goal Progression"

    def __str__(self):
        return "{}".format(self.current_score)

    def _calculate_score(self, digits=2):
        v = 0
        if self.max_total > 0:
            v = round(self.current_total / self.max_total, digits)
        self.current_score = v

    def recalculate_score(self):
        """Recalculate all of the BehaviorProgress values for the current date,
        updating the relevant score-related fields."""
        behavior_ids = self.user.userbehavior_set.values_list("behavior", flat=True)
        start = self.reported_on.replace(hour=0, minute=0, second=0, microsecond=0)
        end = self.reported_on.replace(hour=23, minute=59, second=59, microsecond=999999)
        scores = BehaviorProgress.objects.filter(
            user_behavior__behavior_id__in=behavior_ids,
            user=self.user,
            reported_on__range=(start, end)
        ).values_list('status', flat=True)
        self.current_total = sum(scores)
        self.max_total = len(scores) * BehaviorProgress.ON_COURSE
        self._calculate_score()

    def save(self, *args, **kwargs):
        self._calculate_score()
        return super().save(*args, **kwargs)

    @property
    def text_glyph(self):
        """show a unicode arrow representing the compass needle; used in admin"""
        if self.current_score < 0.25:
            return u"\u2193"  # down (south)
        elif self.current_score >= 0.25 and self.current_score < 0.4:
            return u"\u2198"  # down-right (southeast)
        elif self.current_score >= 0.4 and self.current_score < 0.7:
            return u"\u2192"  # right (east)
        elif self.current_score >= 0.7 and self.current_score < 0.9:
            return u"\u2197"  # right-up (northeast)
        elif self.current_score >= 0.9:
            return u"\u2191"  # up (north)

    objects = GoalProgressManager()


class CategoryProgressManager(models.Manager):
    """Custom manager for the `CategoryProgress` class that includes a method
    to generate scores for a User's progress."""

    def _get_or_update(self, user, category, current_score, current_time):
        # check to see if we've already got a CategoryProgress object for
        # the current date
        start, end = dateutils.date_range(current_time)
        current_score = round(current_score, 2)

        try:
            cp = self.filter(
                user=user,
                category=category,
                reported_on__range=(start, end)
            ).latest()
            cp.current_score = current_score
            cp.save()
        except self.model.DoesNotExist:
            # Create a CategoryProgress object for this data
            cp = self.create(
                user=user,
                category=category,
                current_score=round(current_score, 2),
            )
        return cp

    def generate_scores(self, user):
        created_objects = []
        current_time = timezone.now()

        # Get all the categories that a user has selected IFF there are also
        # some goalprogress objects for that category
        #
        # This is the intersection of:
        # - the set of categories that contain goals that i've selected
        # - the set of categories i've selected
        ug_cats = UserGoal.objects.filter(user=user)
        ug_cats = set(ug_cats.values_list('goal__categories__id', flat=True))
        cat_ids = UserCategory.objects.filter(user=user)
        cat_ids = set(cat_ids.values_list('category__id', flat=True))
        cat_ids = cat_ids.intersection(ug_cats)

        # NOTE: Average GoalProgress for the last 7 days
        start, end = dateutils.date_range(current_time)
        start = start - timedelta(days=7)

        for cat in Category.objects.filter(id__in=cat_ids):
            # Average all latest relevant GoalProgress scores
            results = GoalProgress.objects.filter(
                user=user,
                goal__categories=cat,
                reported_on__range=(start, end)
            ).aggregate(Avg("current_score"))

            # NOTE: Result of averaging the current scores could be None
            current_score = results.get('current_score__avg', 0) or 0

            # Create a CategoryProgress object for this data
            cp = self._get_or_update(user, cat, current_score, current_time)
            created_objects.append(cp.id)
        return self.get_queryset().filter(id__in=created_objects)


class CategoryProgress(models.Model):
    """Agregates score data from `GoalProgress` up to 'today'."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    category = models.ForeignKey(Category)
    current_score = models.FloatField(default=0)
    reported_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reported_on']
        get_latest_by = "reported_on"
        verbose_name = "Category Progress"
        verbose_name_plural = "Category Progression"

    def __str__(self):
        return "{}".format(self.current_score)

    def recalculate_score(self, digits=2):
        """Recalculate all of the Progress values for the current date,
        updating the relevant score-related fields.

        This method Averages the user's GoalProgress scores for all goals
        related to this category, for the most recent day.

        """
        goal_ids = self.category.goals.values_list("id", flat=True)
        start = self.reported_on.replace(hour=0, minute=0, second=0, microsecond=0)
        end = self.reported_on.replace(hour=23, minute=59, second=59, microsecond=999999)
        results = GoalProgress.objects.filter(
            user=self.user,
            goal__id__in=goal_ids,
            reported_on__range=(start, end)
        ).aggregate(Avg("current_score"))
        self.current_score = round(results.get('current_score__avg', 0), digits)

    @property
    def text_glyph(self):
        """show a unicode arrow representing the compass needle; used in admin"""
        if self.current_score < 0.25:
            return u"\u2193"  # down (south)
        elif self.current_score >= 0.25 and self.current_score < 0.4:
            return u"\u2198"  # down-right (southeast)
        elif self.current_score >= 0.4 and self.current_score < 0.7:
            return u"\u2192"  # right (east)
        elif self.current_score >= 0.7 and self.current_score < 0.9:
            return u"\u2197"  # right-up (northeast)
        elif self.current_score >= 0.9:
            return u"\u2191"  # up (north)

    objects = CategoryProgressManager()


class PackageEnrollment(models.Model):
    """A mapping of users who've been enrolled in various *Packaged Content*
    e.g. Categories. This model tracks when they were enrolled, which categories
    they were enrolled in, and who enrolled them.

    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    category = models.ForeignKey(Category)
    goals = models.ManyToManyField(Goal)
    accepted = models.BooleanField(default=False)
    enrolled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='enrolled'
    )
    enrolled_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['enrolled_on']
        verbose_name = "Package Enrollment"
        verbose_name_plural = "Package Enrollments"

    def __str__(self):
        return "{0} enrolled on {1}".format(
            self.user.get_full_name(),
            self.enrolled_on
        )

    # TODO: NEEDS TESTS.
    def create_user_mappings(self):
        """Creates all of the User* mappings for the associated categories and
        all child content."""
        # TODO: this is terribly inefficient, because we'll likely be doing
        # this for a number of users at once.
        try:
            UserCategory.objects.create(user=self.user, category=self.category)
        except IntegrityError:
            pass

        # Enroll the user in the goals.
        goals = self.goals.all()
        for goal in goals:
            try:
                UserGoal.objects.create(user=self.user, goal=goal)
            except IntegrityError:
                pass

        # Enroll the User in the Behaviors
        behaviors = Behavior.objects.published().filter(goals=goals).distinct()
        for behavior in behaviors:
            try:
                UserBehavior.objects.create(user=self.user, behavior=behavior)
            except IntegrityError:
                pass

        # Enroll the User in the Actions
        actions = Action.objects.published().filter(behavior__in=behaviors)
        actions = actions.distinct()
        for action in actions:
            try:
                UserAction.objects.create(user=self.user, action=action)
            except IntegrityError:
                pass

    objects = PackageEnrollmentManager()
