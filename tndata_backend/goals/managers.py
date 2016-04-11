from datetime import datetime

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils import timezone

from .settings import (
    DEFAULT_BEHAVIOR_TRIGGER_NAME,
    DEFAULT_BEHAVIOR_TRIGGER_TIME,
    DEFAULT_BEHAVIOR_TRIGGER_RRULE,
    DEFAULT_MORNING_GOAL_TRIGGER_NAME,
    DEFAULT_MORNING_GOAL_TRIGGER_TIME,
    DEFAULT_MORNING_GOAL_TRIGGER_RRULE,
    DEFAULT_EVENING_GOAL_TRIGGER_NAME,
    DEFAULT_EVENING_GOAL_TRIGGER_TIME,
    DEFAULT_EVENING_GOAL_TRIGGER_RRULE,
)

from utils import user_utils


class CustomActionManager(models.Manager):

    def upcoming(self):
        """Return a queryset of objects that have an upcoming trigger."""
        qs = self.get_queryset()
        return qs.filter(next_trigger_date__gte=timezone.now())

    def stale(self, **kwargs):
        """Return a queryset of objects whose `next_trigger_date` is either
        stale or None."""
        qs = self.get_queryset().filter(**kwargs)
        return qs.filter(
            Q(next_trigger_date__lt=timezone.now()) |
            Q(next_trigger_date=None)
        )


class DailyProgressManager(models.Manager):

    def exists_today(self, user):
        """Check to see if there's already a progress object for today. If so,
        return it's ID (or None)"""
        try:
            start, end = user_utils.local_day_range(user)
            obj = self.filter(user=user, created_on__range=(start, end)).get()
            return obj.id
        except self.model.DoesNotExist:
            return None

    def for_today(self, user):
        """Get/Create the current day's DailyProgress instance for the user"""
        start, end = user_utils.local_day_range(user)
        obj, _ = self.get_or_create(user=user, created_on__range=(start, end))
        return obj


class UserCategoryManager(models.Manager):

    def published(self, *args, **kwargs):
        """Return a QuerySet of UserCategory objects with at least one
        published category.

        By default, this also includes pacakged content.

        """
        qs = super().get_queryset()
        qs = qs.filter(category__state='published')
        return qs.filter(**kwargs).distinct()


class UserGoalManager(models.Manager):

    def published(self, *args, **kwargs):
        """Return a QuerySet of UserGoal objects with at least one
        published Goal.

        """
        qs = super().get_queryset()
        qs = qs.filter(goal__state='published')
        return qs.filter(**kwargs).distinct()


class UserBehaviorManager(models.Manager):

    def published(self, *args, **kwargs):
        """Return a QuerySet of UserBehavior objects with at least one
        published Behavior.

        """
        qs = super().get_queryset()
        qs = qs.filter(behavior__state='published')
        return qs.filter(**kwargs).distinct()


class UserActionQuerySet(models.QuerySet):
    """QuerySet methods to filter UserActions; these are accessed through
    the UserActionManager, but implemented as a QuserySet subclass so they
    can be chained.

    """
    def published(self, **kwargs):
        qs = self.filter(action__state='published').filter(**kwargs)
        return qs.distinct()

    def upcoming(self):
        return self.filter(next_trigger_date__gte=timezone.now())

    def stale(self, **kwargs):
        return self.filter(**kwargs).filter(
            Q(next_trigger_date__lt=timezone.now()) |
            Q(next_trigger_date=None)
        )


class UserActionManager(models.Manager):

    def get_queryset(self):
        return UserActionQuerySet(self.model, using=self._db)

    def published(self, **kwargs):
        """Return a QuerySet of UserAction objects with at least one
        published Action.

        """
        return self.get_queryset().published(**kwargs)

    def upcoming(self):
        """Return a queryset UserActions that have an upcoming trigger."""
        return self.get_queryset().upcoming()

    def stale(self, **kwargs):
        """Return a queryset of UserActions whose `next_trigger_date` is either
        stale or None."""
        return self.get_queryset().stale(**kwargs)

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
        trigger, but whose Action does include a default trigger."""
        qs = self.get_queryset()
        return qs.filter(
            custom_trigger__isnull=True,
            action__default_trigger__isnull=False,
        )

    def select_from_bucket(self, bucket, *args, **kwargs):
        """Returns a queryset of UserActions that are listed within the given
        bucket. This method also restricts its results to published Actions.

        - bucket: The bucket from which to pull a UserAction (ss Action.bucket)
        - exclude_completed: A boolean, if provided as a keyword argument,
          this will excluded actions that have a corresponding
          UserCompletedAction whose status is COMPLETED. The default is True.

        Usage:

            UserAction.objects.select_from_bucket('core', user=some_user)
        or:
            user.useraction_set.select_from_bucket('core')

        ----

        **Support for `Action.sequence_order`**

        This method respects the Action.sequence_order value, in that it will
        filter results based on the lowest-value from un-completed Actions. For
        example, we will only return items whose sequence_order is 0, until all
        those are completed, at which point this method will only return results
        whose sequence_order is 1, etc.

        This filter is applied _after_ the bucket filter, so we still only
        pull from a single bucket at a time.

        """
        from .models import UserCompletedAction as UCA
        exclude_completed = kwargs.pop('exclude_completed', True)

        # The accepted or public UserActions that are in the given bucket
        qs = self.get_queryset().filter(*args, **kwargs)
        qs = qs.filter(
            action__state='published',
            action__behavior__state='published',
            action__bucket=bucket
        )

        if exclude_completed:
            qs = qs.exclude(usercompletedaction__state=UCA.COMPLETED)

        # Respect Action.sequence_order.
        # Look at the `sequence_order` values (which should be ordered,
        # low-to-high), and pick the first value and filter on that.
        sequences = qs.values_list('action__sequence_order', flat=True)
        if len(sequences) > 0:
            qs = qs.filter(action__sequence_order=sequences[0])

        return qs


class TriggerManager(models.Manager):
    """A simple manager for the Trigger model. This class adds a few convenience
    methods to the regular api:

    * get_default_behavior_trigger() -- returns the default trigger for
      `Behavior` reminders.
    * get_default_morning_goal_trigger() -- returns the default trigger for the
      morning Goal reminder.
    * get_default_evening_goal_trigger() -- returns the default trigger for the
      evening Goal reminder.
    * custom() -- the set of Triggers that are associated with a user
    * default() -- the set of default Triggers (not associated with a user)
    * for_user(user) -- returns all the triggers for a specific user.

    """

    def get_default_behavior_trigger(self):
        """Retrieve (or create) the default Behavior trigger.
        """
        try:
            slug = slugify(DEFAULT_BEHAVIOR_TRIGGER_NAME)
            trigger = self.default(name_slug=slug).first()
            assert trigger is not None
            return trigger
        except (self.model.DoesNotExist, AssertionError):
            trigger_time = datetime.strptime(DEFAULT_BEHAVIOR_TRIGGER_TIME, "%H:%M")
            trigger_time = trigger_time.time().replace(tzinfo=timezone.utc)
            return self.model.objects.create(
                name=DEFAULT_BEHAVIOR_TRIGGER_NAME,
                time=trigger_time,
                recurrences=DEFAULT_BEHAVIOR_TRIGGER_RRULE,

            )

    def get_default_morning_goal_trigger(self):
        """Retrieve (or create) the default morning Goal trigger."""
        try:
            slug = slugify(DEFAULT_MORNING_GOAL_TRIGGER_NAME)
            trigger = self.default(name_slug=slug).first()
            assert trigger is not None
            return trigger
        except (self.model.DoesNotExist, AssertionError):
            trigger_time = datetime.strptime(DEFAULT_MORNING_GOAL_TRIGGER_TIME, "%H:%M")
            trigger_time = trigger_time.time().replace(tzinfo=timezone.utc)
            return self.model.objects.create(
                name=DEFAULT_MORNING_GOAL_TRIGGER_NAME,
                time=trigger_time,
                recurrences=DEFAULT_MORNING_GOAL_TRIGGER_RRULE,
            )

    def get_default_evening_goal_trigger(self):
        try:
            slug = slugify(DEFAULT_EVENING_GOAL_TRIGGER_NAME)
            trigger = self.default(name_slug=slug).first()
            assert trigger is not None
            return trigger
        except (self.model.DoesNotExist, AssertionError):
            trigger_time = datetime.strptime(DEFAULT_EVENING_GOAL_TRIGGER_TIME, "%H:%M")
            trigger_time = trigger_time.time().replace(tzinfo=timezone.utc)
            return self.model.objects.create(
                name=DEFAULT_EVENING_GOAL_TRIGGER_NAME,
                time=trigger_time,
                recurrences=DEFAULT_EVENING_GOAL_TRIGGER_RRULE,
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
        if user.is_authenticated():
            return self.get_queryset().filter(user=user)
        return self.get_queryset().none()

    def create_for_user(self, user, name, time, date, rrule,
                        obj=None, disabled=False):
        """Creates a time-type trigger based on the given RRule data."""
        # Ensure that we associate any new Triggers with a related object
        # (e.g. UserAction.custom_trigger?)

        trigger = self.create(
            user=user,
            name=name,
            time=time,
            trigger_date=date,
            recurrences=rrule,
            disabled=disabled,
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
        kwargs['state'] = 'published'
        return self.get_queryset().filter(**kwargs)


class BehaviorManager(WorkflowManager):

    def contains_dynamic(self):
        """Return a queryset of Behaviors that contain dynamic notifications,
        i.e. Actions that have a bucket, and whose default trigger contains
        a time_of_day and frequency value.

        NOTE: These behaviors may also contain some NON-Dynamic actions, as well.

        """
        return self.filter(
            action__default_trigger__time_of_day__isnull=False,
            action__default_trigger__frequency__isnull=False
        ).distinct()

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
        qs = super().get_queryset().filter(packaged_content=True)
        if published:
            qs = qs.filter(packaged_content=True, state="published")
        return qs.distinct()


class GoalManager(WorkflowManager):

    def published(self, *args, **kwargs):
        """Returns Goals that are published and are contained within non-packaged
        categories (that are also published)."""
        goals = super().published()
        # We want to omit goals that are *only* in packages, but not those that
        # might be in both public categories & packages; Therefore we need to
        # use `categories__packaged_content=False` rather than .exclude(...)
        goals = goals.filter(
            categories__state='published',
            categories__packaged_content=False
        )
        return goals.distinct()

    def packages(self, *args, **kwargs):
        """Return only Categories that have been marked as packages.

        By default this returns only published categories; pass in
        `published=False` to return all packaged content.

            Category.objects.packages(published=False)

        """
        published = kwargs.pop("published", True)
        qs = super().get_queryset()
        if published:
            qs = qs.filter(categories__packaged_content=True, state="published")
        else:
            qs = qs.filter(categories__packaged_content=True)
        return qs.filter(**kwargs).distinct()


class PackageEnrollmentManager(models.Manager):

    def batch_enroll(self, emails, category, goals, by, prevent_triggers=False):
        """Given a list of email addresses, get or create PackageEnrollments
        for them. Returns a QuerySet of PackageEnrollment objects.

        """
        # NOTE: this doesn't create duplicate PackageEnrollments, but it does
        # udpate a user's goals.
        created_objects = []
        User = get_user_model()

        for email in emails:
            email = email.strip().lower()
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                # Create an inactive user. This will:
                #
                # - Ensure they still go thru onboarding in the app.
                # - Allow them to later set their password and user fields.
                user = user_utils.create_inactive_user(email)

            try:
                enrollment = self.get(user=user, category=category)
                enrollment.enrolled_by = by
                enrollment.prevent_custom_triggers = prevent_triggers
                enrollment.save()
            except self.model.DoesNotExist:
                enrollment = self.create(
                    user=user,
                    category=category,
                    enrolled_by=by,
                    prevent_custom_triggers=prevent_triggers
                )

            # Will add new goals or update the existing relationships.
            for goal in goals:
                enrollment.goals.add(goal)
            enrollment.save()

            # If a user has accepted this package already, go ahead and add
            # their content. They'll receive an email notifying them about the
            # new goals, but they won't have to accept them.
            if enrollment.accepted:
                enrollment.create_user_mappings()

            created_objects.append(enrollment.id)

        return self.get_queryset().filter(pk__in=created_objects)
