from datetime import datetime

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .settings import (
    DEFAULT_BEHAVIOR_TRIGGER_NAME,
    DEFAULT_BEHAVIOR_TRIGGER_TIME,
    DEFAULT_BEHAVIOR_TRIGGER_RRULE,
)

from utils import user_utils


class UserCategoryManager(models.Manager):

    def published(self, *args, **kwargs):
        """Return a QuerySet of UserCategory objects with at least one
        published category.

        By default, this also includes pacakged content.

        """
        qs = super().get_queryset()
        qs = qs.filter(category__state='published')
        return qs.filter(**kwargs).distinct()

    def accepted_or_public(self, user):
        """Return UserCategory instances for Categories that are,

        1. Public (the user opted into)
        2. Packages that the user has accepted.

        """
        if not user.is_authenticated():
            return self.get_queryset().none()

        # The user's UserCategory instances
        qs = self.published().filter(user=user)

        # Category IDs that have NOT been accepted by the user
        ids = user.packageenrollment_set.filter(accepted=False)
        ids = ids.values_list("category", flat=True)

        # Result: Exclude those un-accepted categories
        return qs.exclude(category__id__in=ids)


class UserGoalManager(models.Manager):

    def published(self, *args, **kwargs):
        """Return a QuerySet of UserGoal objects with at least one
        published Goal.

        """
        qs = super().get_queryset()
        qs = qs.filter(goal__state='published')
        return qs.filter(**kwargs).distinct()

    def accepted_or_public(self, user):
        """Return UserGoal instances for goals that are in public or accepted
        categories/packages.

        """
        if not user.is_authenticated():
            return self.get_queryset().none()

        # The user's selected Goal instances
        qs = self.published().filter(user=user)

        # Category IDs that have NOT been accepted by the user
        ids = user.packageenrollment_set.filter(accepted=False)
        ids = ids.values_list("category", flat=True)

        # Result: Exclude those un-accepted categories
        return qs.exclude(goal__categories__id__in=ids)


class UserBehaviorManager(models.Manager):

    def published(self, *args, **kwargs):
        """Return a QuerySet of UserBehavior objects with at least one
        published Behavior.

        """
        qs = super().get_queryset()
        qs = qs.filter(behavior__state='published')
        return qs.filter(**kwargs).distinct()

    def accepted_or_public(self, user):
        """Return UserBehavior instances for behaviors that are in public or
        accepted categories/packages.

        """
        if not user.is_authenticated():
            return self.get_queryset().none()

        # The user's selected Behavior instances
        qs = self.published().filter(user=user)

        # Category IDs that have NOT been accepted by the user
        ids = user.packageenrollment_set.filter(accepted=False)
        ids = ids.values_list("category", flat=True)

        # Result: Exclude those un-accepted categories
        return qs.exclude(behavior__goals__categories__in=ids)


class UserActionManager(models.Manager):

    def published(self, *args, **kwargs):
        """Return a QuerySet of UserAction objects with at least one
        published Action.

        """
        qs = super().get_queryset()
        qs = qs.filter(action__state='published')
        return qs.filter(**kwargs).distinct()

    def upcoming(self):
        """Return a queryset UserActions that have an upcoming trigger."""
        qs = self.get_queryset()
        return qs.filter(next_trigger_date__gte=timezone.now())

    def stale(self):
        """Return a queryset of UserActions whose `next_trigger_date` is either
        stale or None."""
        qs = self.get_queryset()
        return qs.filter(
            Q(next_trigger_date__lt=timezone.now()) |
            Q(next_trigger_date=None)
        )

    def accepted_or_public(self, user):
        """Return UserAction instances for actions that are in public or
        accepted categories/packages.

        """
        if not user.is_authenticated():
            return self.get_queryset().none()

        # The user's selected Action instances
        qs = self.published().filter(user=user)

        # Category IDs that have NOT been accepted by the user
        ids = user.packageenrollment_set.filter(accepted=False)
        ids = ids.values_list("category", flat=True)

        # Result: Exclude those un-accepted categories
        return qs.exclude(action__behavior__goals__categories__in=ids)

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


class GoalManager(WorkflowManager):

    def published(self, *args, **kwargs):
        """Returns Goals that are published and are contained within non-packaged
        categories (that are also published)."""
        goals = super().published()
        goals = goals.filter(categories__state='published')
        goals = goals.exclude(categories__packaged_content=True)
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
        return qs.filter(**kwargs)


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
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Create an inactive user. This will:
                #
                # - Ensure they still go thru onboarding in the app.
                # - Allow them to later set their password and user fields.
                user = user_utils.create_inactive_user(email)

            try:
                # obj == a PackageEnrollment
                obj = self.get(user=user, category=category)
                obj.enrolled_by = by
                obj.prevent_custom_triggers = prevent_triggers
                obj.save()
            except self.model.DoesNotExist:
                obj = self.create(
                    user=user,
                    category=category,
                    enrolled_by=by,
                    prevent_custom_triggers=prevent_triggers
                )

            # Will add new goals or update the existing relationships.
            for goal in goals:
                obj.goals.add(goal)
            obj.save()

            # If a user has accepted this package already, go ahead and add
            # their content. They'll receive an email notifying them about the
            # new goals, but they won't have to accept them.
            if obj.accepted:
                obj.create_user_mappings()

            created_objects.append(obj.id)

        return self.get_queryset().filter(pk__in=created_objects)
