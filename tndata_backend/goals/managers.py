from datetime import datetime, timedelta

import logging
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Min, Q
from django.template.defaultfilters import slugify
from django.utils import timezone

from .settings import (
    DEFAULT_MORNING_GOAL_TRIGGER_NAME,
    DEFAULT_MORNING_GOAL_TRIGGER_TIME,
    DEFAULT_MORNING_GOAL_TRIGGER_RRULE,
    DEFAULT_EVENING_GOAL_TRIGGER_NAME,
    DEFAULT_EVENING_GOAL_TRIGGER_TIME,
    DEFAULT_EVENING_GOAL_TRIGGER_RRULE,
)

from utils import dateutils, user_utils


logger = logging.getLogger(__name__)


class CustomActionManager(models.Manager):

    def upcoming(self):
        """Return a queryset of objects that have an upcoming trigger."""
        qs = self.get_queryset()
        return qs.filter(next_trigger_date__gte=timezone.now())

    def stale(self, **kwargs):
        """Return a queryset of objects whose `next_trigger_date` is either
        stale or None."""
        hours = kwargs.pop('hours', None)
        now = timezone.now()

        qs = self.get_queryset().filter(**kwargs).filter(
            Q(next_trigger_date__lt=now) |
            Q(next_trigger_date=None)
        )
        if hours:
            threshold = now - timedelta(hours=hours)
            qs = qs.filter(updated_on__lte=threshold)
        return qs


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
        try:
            obj = self.get(user=user, created_on__range=(start, end))
        except self.model.MultipleObjectsReturned:
            # This is not supposed to happen but it did. Just resturn the
            # first item and log it.
            msg = "MultipleObjectsReturned for DailyProgress; user.id = {}"
            logger.warning(msg.format(user.id))
            obj = self.filter(user=user, created_on__range=(start, end))[0]
        except self.model.DoesNotExist:
            obj = self.create(user=user)
        return obj

    def engagement_rank(self, user):
        """Given a user, find out how their 15-day engagement stats compare
        with other users.

        Strategy for doing this:

        1. Get the user's latest DailyProgress
        2. Filter all other DailyProgress objects within that range.
        3. Calculate the user's engagement_15_days value compared with others
           on the same day. Do do this, we count the number of values below
           the user's divided by the total number of values

        """
        try:
            dp = self.filter(user=user).latest()

            daterange = dateutils.date_range(dp.created_on)
            values = self.filter(created_on__range=daterange)
            total = values.count()
            values = values.values_list('engagement_15_days', flat=True)
            values = sorted(values, reverse=True)  # Sort biggest -> smallest

            # Find the first occurance of the user's value, and count the rest.
            num_lower = len(values[values.index(dp.engagement_15_days) + 1:])
            return round((num_lower / total) * 100, 2)

        except (self.model.DoesNotExist, IndexError, ZeroDivisionError):
            return 0.0


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

    def next_in_sequence(self, **kwargs):
        """Return a queryset of UserGoals that are:

        - not completed,
        - the next in the sequence (based on sequence_order)

        """
        # Allow a published=True kwarg
        if kwargs.pop('published', False):
            kwargs['goal__state'] = 'published'

        kwargs['completed'] = False
        qs = self.get_queryset().filter(**kwargs)
        seq = qs.aggregate(Min('goal__sequence_order'))
        seq = seq.get('goal__sequence_order__min') or 0
        return qs.filter(goal__sequence_order=seq)

    def latest_items(self, user=None):
        """Return a queryset of the most recent UserGoal objects per user."""
        if user:
            try:
                params = [user.id]
            except AttributeError:  # assume user is an ID.
                params = [user]
            sql = (
                "SELECT id, user_id, goal_id, MAX(created_on) "
                "FROM goals_usergoal WHERE user_id=%s "
                "GROUP BY id, user_id, goal_id "
                "ORDER BY user_id ASC, goal_id ASC"
            )
        else:
            params = None
            sql = (
                "SELECT id, user_id, goal_id, MAX(created_on) "
                "FROM goals_usergoal GROUP BY id, user_id, goal_id "
                "ORDER BY user_id ASC, goal_id ASC"
            )
        return self.raw(sql, params)

    def engagement_rank(self, user, goal):
        """Given a user and a goal, find out how their 15-day engagement stats
        compare with other users within that goal.

        Strategy for doing this:

        1. Get the user's latest UserGoal object
        2. Get all other UserGoal objects within that date range.
        3. Calculate the user's engagement_15_days value compared with others
           on the same day. To do this, we count the number of values below
           the user's divided by the total number of values

        """
        try:
            ug = self.filter(user=user, goal=goal).latest('created_on')

            daterange = dateutils.date_range(ug.created_on)
            # XXX: let's pull in a couple days worth of data, because it's
            # likely that we may not get enough values to compare.
            daterange = (daterange[0] - timedelta(days=2), daterange[1])
            values = self.filter(goal=goal, created_on__range=daterange)
            total = values.count()
            values = values.values_list('engagement_15_days', flat=True)
            values = sorted(values, reverse=True)  # Sort biggest -> smallest

            # Find the first occurance of the user's value, and count the rest.
            if len(values) > 2:
                num_lower = len(values[values.index(ug.engagement_15_days) + 1:])
                return round((num_lower / total) * 100, 2)
            # If there's only 1 or 2 values, let's fudge this a bit. 1 value
            # would put us at 100, but 2 at 50. 90% seems a good compromise in
            # those cases.
            return 90.0
        except (self.model.DoesNotExist, IndexError, ZeroDivisionError):
            return 0.0


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
        """Returns UserAction objects whose `next_trigger_date` is in the past.

        An `hours` parameter will limit results to objects that are older
        than the given number of hours, e.g. hours=2 will give us items that
        are at least 2 hours old.

        """
        hours = kwargs.pop('hours', None)
        now = timezone.now()

        # Items with no trigger, or whose trigger is in the past.
        qs = self.filter(**kwargs).filter(
            Q(next_trigger_date__lt=now) |
            Q(next_trigger_date=None)
        )
        # Items that haven't been updated in some time threshold
        if hours:
            threshold = now - timedelta(hours=hours)
            qs = qs.filter(updated_on__lte=threshold)

        return qs


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

    def next_in_sequence(self, **kwargs):
        """Return the queryset of UserActions that have not yet been completed
        and are 'up next' based on the sequence order.

        Possible arguments:

        * goals - Either a queryset or iterable of Goals or Goal IDS. This will
                  filter UserActions related to the given Goal(s).
        * published - (optional). You may provide `published=True` as a keyword
                      argument, and this method will only return objects related
                      to published Actions.

        """
        from .models import UserCompletedAction as UCA
        goals = kwargs.pop('goals', None)  # see if we're filtering on goals.
        if kwargs.pop('published', False):  # or if we want published content
            kwargs['action__state'] = 'published'

        # Get the UserActions, excluding those that have been completed
        qs = self.get_queryset().filter(**kwargs)
        qs = qs.exclude(usercompletedaction__state=UCA.COMPLETED)
        if goals:
            qs = qs.filter(primary_goal__in=goals)

        # get the smallest sequence order...
        min_order = qs.aggregate(Min('action__sequence_order'))
        min_order = min_order.get('action__sequence_order__min') or 0

        # Return those that match.
        return qs.filter(action__sequence_order=min_order)


class TriggerManager(models.Manager):
    """A simple manager for the Trigger model. This class adds a few convenience
    methods to the regular api:

    * get_default_morning_goal_trigger() -- returns the default trigger for the
      morning Goal reminder.
    * get_default_evening_goal_trigger() -- returns the default trigger for the
      evening Goal reminder.
    * custom() -- the set of Triggers that are associated with a user
    * default() -- the set of default Triggers (not associated with a user)
    * for_user(user) -- returns all the triggers for a specific user.

    """
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


class WorkflowQuerySet(models.QuerySet):
    def for_contributor(self, user):
        """Filter the queryset based on whether or not the user is a contributor
        in a Category."""

        # To do this, we need different lookups based on the type of object.
        lookups = {
            'category': 'contributors',
            'goal': 'categories__contributors',
            'action': 'goals__categories__contributors',
        }
        lookup = {lookups[self.model.__name__.lower()]: user}
        return self.filter(**lookup).distinct()


class WorkflowManager(models.Manager):
    """A simple model manager for those models that include a workflow
    `state` field. This adds a convenience method for querying published
    objects.

    """
    def get_queryset(self):
        return WorkflowQuerySet(self.model, using=self._db)

    def published(self, *args, **kwargs):
        kwargs['state'] = 'published'
        return self.get_queryset().filter(**kwargs)

    def for_contributor(self, user):
        qs = self.get_queryset()
        return qs.filter(contributors=user)


class CategoryManager(WorkflowManager):
    """Updated WorkflowManager for Categories; we want to exclude packaged
    content from the list of published Categories."""

    def published(self, *args, **kwargs):
        qs = super().published()
        return qs.filter(packaged_content=False)

    def selected_by_default(self, **kwargs):
        """Return a queryset of Categories that should be selected by default."""
        kwargs['selected_by_default'] = True
        return super().get_queryset().filter(**kwargs)

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


class UserCompletedActionManager(models.Manager):

    def engagement(self, user, goal=None, days=15):
        """Measures a user's "engagement" within the app over some time period
        (default of 15 days). Engagment is calculated as:

            Completed UserCompletedActions / Total UserCompletedActions

        - `user`: The user for whom engagement is calculated.
        - `goal`: If given, the calculation will be restricted to this Goal
          i.e. it filters on UserAction.primary_goal
        - `days`: Integer number of days over which we calculate (default is 15)

        """
        result = 0.0
        since = timezone.now() - timedelta(days=days)

        # Count number of completed / total items over some timeframe
        qs = self.get_queryset().filter(user=user, created_on__gte=since)
        if goal is not None:
            qs = qs.filter(useraction__primary_goal=goal)

        total = qs.count()
        if total > 0:
            completed = qs.filter(state=self.model.COMPLETED).count()
            result = round((completed / total) * 100, 2)

        return result
