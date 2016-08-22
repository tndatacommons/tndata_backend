from collections import defaultdict
from datetime import datetime, timedelta

import logging
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Min, Q
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
from utils.datastructures import flatten


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


class UserBehaviorManager(models.Manager):

    def published(self, *args, **kwargs):
        """Return a QuerySet of UserBehavior objects with at least one
        published Behavior.

        """
        qs = super().get_queryset()
        qs = qs.filter(behavior__state='published')
        return qs.filter(**kwargs).distinct()

    def next_in_sequence(self, **kwargs):
        """Return a queryset of UserBehaviors that are:

        - not completed,
        - the next in the sequence (based on sequence_order)

        Allowed keyword arguments include:

        - published -- restrict results to published Behaviors
        - goals -- filters by goals.

        """
        # Allow a published=True kwarg
        if kwargs.pop('published', False):
            kwargs['behavior__state'] = 'published'
        kwargs['completed'] = False

        # Filter on provided goals (if any)
        goals = kwargs.pop('goals', None)
        if goals:
            kwargs['behavior__goals__in'] = goals
        qs = self.get_queryset().select_related('behavior').filter(**kwargs)

        # ---------------------------------------------------------------------
        # NOTE: We need to make the minimum sequence_order values dependent on
        # the behavior's parent goals. For example, I may be in Goal A (seq 0),
        # but also in Goal B (seq 1), and Goal A's min sequence value might be
        # 0 while Goal B's min sequence value might be 1. We can't exclude the
        # Behaviors in Goal B.
        #
        # To do this, we need to determine what the min Behavior.sequence_order
        # is for each goal.
        # ---------------------------------------------------------------------
        #
        # populate data, like:
        #
        # {
        #   goal_id: [(behavior_id, sequence_order)]
        #   ...
        # }
        #
        # THEN, filter on the minimum sequence_order value for each goal, and
        # flatten the  remaining behavior_ids, and return a queryset of
        # matching those behavior ids.
        # ---------------------------------------------------------------------
        if goals is None and hasattr(self, 'instance') and self.instance:
            # If we werent' given any goals, use those selected by the user.
            goals = self.instance.usergoal_set.next_in_sequence()
            goals = goals.values_list("goal", flat=True)
        elif goals is None:
            # No user, use all of the behaviors' parent goals.
            goals = set(flatten(ub.behavior.goal_ids for ub in qs))

        sequences_by_goal = defaultdict(set)
        for goal_id in goals:
            for ub in qs:
                if goal_id in ub.behavior.goal_ids:
                    sequences_by_goal[goal_id].add(
                        (ub.behavior_id, ub.behavior.sequence_order)
                    )

        # Now find the min sequence value per goal & filter out the others.
        for goal_id, values in sequences_by_goal.items():
            min_seq = min(t[1] for t in values)
            sequences_by_goal[goal_id] = [t[0] for t in values if t[1] == min_seq]

        # Flatten that list
        behavior_ids = list(flatten(sequences_by_goal.values()))
        return qs.filter(behavior__id__in=behavior_ids)


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

    def next_in_sequence(self, behaviors, **kwargs):
        """Given a behavior, return the queryset of UserActions that are
        related to the behavior, but have not yet been completed, and are
        the next in a sequence.

        * behaviors - Either a Behavior instance, a queryset of Behaviors, or
                      an iterable of Behavior IDs. This will filter UserActions
                      related to the given Behavior(s).
        * published - (optional). You may provide `published=True` as a keyword
                      argument, and this method will only return objects related
                      to published Actions.

        """
        from .models import UserCompletedAction as UCA
        sequences_by_behavior = {}

        if kwargs.pop('published', False):
            kwargs['action__state'] = 'published'

        is_behavior_object = (
            hasattr(behaviors, '__class__') and
            behaviors.__class__.__name__ == "Behavior"
        )
        if is_behavior_object:
            kwargs['action__behavior'] = behaviors
            sequences_by_behavior = {b.id: set() for b in behaviors}
        else:
            kwargs['action__behavior__in'] = behaviors
            sequences_by_behavior = {bid: set() for bid in behaviors}

        qs = self.get_queryset().filter(**kwargs)

        # Then exluded the ones we've marked as completed.
        qs = qs.exclude(usercompletedaction__state=UCA.COMPLETED)

        # Now, find the minimum sequence_order value, based for the set of
        # actions in each parent behavior.
        for ua in qs:
            sequences_by_behavior[ua.action.behavior_id].add(
                (ua.action_id, ua.action.sequence_order)
            )

        # Now find the min sequence value per behavior & filter out the others.
        for behavior_id, values in sequences_by_behavior.items():
            try:
                min_seq = min(t[1] for t in values)
                sequences_by_behavior[behavior_id] = [
                    t[0] for t in values if t[1] == min_seq
                ]
            except ValueError:
                pass  # min() might fail if there are no values

        # Flatten that list & do a lookup
        action_ids = list(flatten(sequences_by_behavior.values()))
        return qs.filter(action__pk__in=action_ids)


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


class WorkflowQuerySet(models.QuerySet):
    def for_contributor(self, user):
        """Filter the queryset based on whether or not the user is a contributor
        in a Category."""

        # To do this, we need different lookups based on the type of object.
        lookups = {
            'category': 'contributors',
            'goal': 'categories__contributors',
            'behavior': 'goals__categories__contributors',
            'action': 'behavior__goals__categories__contributors',
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
