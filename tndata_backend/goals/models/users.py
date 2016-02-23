"""
Mappings between users and their selected public content.

    [Category] <-> [Goal] <-> [Behavior] <- [Action]
        |            |            |            |
  [UserCategory] [UserGoal]  [UserBehavior] [UserAction]
        \            \            /            /
         \            \          /            /

                        [ User ]

"""
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from jsonfield import JSONField
from utils.user_utils import local_day_range, to_localtime, to_utc

from .misc import _custom_triggers_allowed
from .public import Action, Behavior, Category, Goal
from .triggers import Trigger
from ..encoder import dump_kwargs
from ..managers import (
    UserActionManager,
    UserBehaviorManager,
    UserCategoryManager,
    UserGoalManager,
)


class UserCategory(models.Model):
    """This model maps a User with their selected Categories."""
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

    @property
    def custom_triggers_allowed(self):
        """Check to see if the user/category is a Package where custom triggers
        are restricted."""
        return _custom_triggers_allowed(self.user, self)

    def get_user_goals(self):
        """Returns a QuerySet of published Goals related to this Category, but
        restricts those goals to those which the user has selected."""
        gids = self.user.usergoal_set.values_list('goal__id', flat=True)
        return self.category.goals.filter(id__in=gids, state='published')

    @property
    def progress_value(self):
        return 0.0

    objects = UserCategoryManager()


class UserGoal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    goal = models.ForeignKey(Goal)
    primary_category = models.ForeignKey(
        Category,
        blank=True,
        null=True,
        help_text="A primary category associated with the Goal. Typically this "
                  "is the Category through which the goal was selected."
    )
    completed = models.BooleanField(default=False)
    completed_on = models.DateTimeField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    # Pre-rendered FK Fields.
    serialized_goal = JSONField(blank=True, default=dict, dump_kwargs=dump_kwargs)
    serialized_goal_progress = JSONField(blank=True, default=dict, dump_kwargs=dump_kwargs)
    serialized_user_categories = JSONField(blank=True, default=dict, dump_kwargs=dump_kwargs)
    serialized_user_behaviors = JSONField(blank=True, default=dict, dump_kwargs=dump_kwargs)
    serialized_primary_category = JSONField(blank=True, default=dict, dump_kwargs=dump_kwargs)

    class Meta:
        ordering = ['user', 'goal']
        unique_together = ("user", "goal")
        verbose_name = "User Goal"
        verbose_name_plural = "User Goals"

    def __str__(self):
        return "{0}".format(self.goal.title)

    def save(self, *args, **kwargs):
        self._serialize_goal()
        self._serialize_user_behaviors()
        self._serialize_user_categories()
        self._serialize_primary_category()
        return super().save(*args, **kwargs)

    def _serialize_goal(self):
        if self.goal:
            from ..serializers.simple import SimpleGoalSerializer
            self.serialized_goal = SimpleGoalSerializer(self.goal, user=self.user).data

    def _serialize_user_categories(self):
        cats = self.get_user_categories()
        if cats:
            from ..serializers.simple import SimpleCategorySerializer
            self.serialized_user_categories = SimpleCategorySerializer(cats, many=True).data

    def _serialize_user_behaviors(self):
        behaviors = self.get_user_behaviors()
        if behaviors:
            from ..serializers.simple import SimpleBehaviorSerializer
            self.serialized_user_behaviors = SimpleBehaviorSerializer(behaviors, many=True).data

    def _serialize_primary_category(self):
        cat = self.get_primary_category()
        if cat:
            from ..serializers.simple import SimpleCategorySerializer
            self.serialized_primary_category = SimpleCategorySerializer(cat).data

    @property
    def goal_progress(self):
        return None

    @property
    def custom_triggers_allowed(self):
        """Check to see if the user/goal is in a Package where custom triggers
        are restricted. """
        return _custom_triggers_allowed(self.user, self)

    def get_user_behaviors(self):
        """Returns a QuerySet of published Behaviors related to this Goal, but
        restricts those behaviors to those which the user has selected.

        """
        bids = self.user.userbehavior_set.values_list('behavior_id', flat=True)
        return self.goal.behavior_set.filter(id__in=bids, state='published')

    def get_user_categories(self):
        """Returns a QuerySet of published Categories related to this Goal, but
        restricts those categories to those which the user has selected.

        """
        cids = self.user.usercategory_set.values_list('category__id', flat=True)
        return self.goal.categories.filter(id__in=cids, state='published')

    def get_primary_category(self):
        """Return the first user-selected category that is a
        parent of this goal."""
        if self.primary_category:
            return self.primary_category

        cat = self.get_user_categories().first()
        if cat is None:
            cat = self.goal.categories.first()
        self.primary_category = cat
        return cat

    @property
    def progress_value(self):
        return 0.0

    objects = UserGoalManager()


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

    @property
    def behavior_progress(self):
        return None

    @property
    def custom_triggers_allowed(self):
        """Check to see if the user/behavior is the child of a goal within a
        Package where custom triggers are restricted. """
        return _custom_triggers_allowed(self.user, self)

    def get_user_categories(self):
        """Returns a QuerySet of published Categories related to this Behavior,
        but restricts the result to those Categories which the user has selected.

        """
        # User-selected categories
        a = set(self.user.usercategory_set.values_list('category__id', flat=True))
        # Parent categories (through goals)
        b = set(self.behavior.goals.values_list("categories", flat=True))
        # The overlap
        ids = a.intersection(b)
        return Category.objects.published().filter(id__in=ids)

    def get_user_goals(self):
        """Returns a QuerySet of published Goals related to this Behavior, but
        restricts those goals to those which the user has selected."""
        gids = self.user.usergoal_set.values_list('goal__id', flat=True)
        return self.behavior.goals.filter(id__in=gids, state='published')

    def get_custom_trigger_name(self):
        """This should generate a unique name for this object's custom
        trigger."""
        return "custom trigger for userbehavior-{0}".format(self.id)

    def get_useractions(self):
        """Returns a QuerySet of UserAction objects whose Action is a child of
        this object's associated Behavior.
        """
        return self.user.useraction_set.filter(action__behavior=self.behavior)

    def get_actions(self):
        """Returns a QuerySet of published Actions related to this Behavior, but
        restricts the results to those which the user has selected.

        """
        uids = self.user.useraction_set.values_list('action_id', flat=True)
        return self.behavior.action_set.filter(id__in=uids, state='published')

    objects = UserBehaviorManager()


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
    next_trigger_date = models.DateTimeField(
        blank=True,
        null=True,
        editable=False,
        help_text="The next date/time that a notification for this action "
                  "will be triggered (this is auto-populated and is in UTC)."
    )
    # In order to calculate "today's stats" for completed vs incomplete
    # actions, we need to be able to query backwards at least a day to find
    # actions that were scheduled in the past 24 hours.
    prev_trigger_date = models.DateTimeField(
        blank=True,
        null=True,
        editable=False,
        help_text="The previous date/time that a notification for this action "
                  "was be triggered (this is auto-populated and is in UTC)."
    )
    primary_category = models.ForeignKey(
        Category,
        blank=True,
        null=True,
        help_text="A primary category associated with this action. Typically this "
                  "is the parent category of the primaary goal."
    )
    primary_goal = models.ForeignKey(
        Goal,
        blank=True,
        null=True,
        help_text="A primary goal associated with this action. Typically this "
                  "is the goal through which a user navigated to find the action."
    )

    # Pre-rendered FK Fields.
    serialized_action = JSONField(blank=True, default=dict, dump_kwargs=dump_kwargs)
    serialized_behavior = JSONField(blank=True, default=dict, dump_kwargs=dump_kwargs)
    # TODO: deprecate this field in favor of only using `serialized_trigger`
    serialized_custom_trigger = JSONField(blank=True, default=dict, dump_kwargs=dump_kwargs)
    serialized_primary_goal = JSONField(blank=True, default=dict, dump_kwargs=dump_kwargs)
    serialized_primary_category = JSONField(blank=True, default=dict, dump_kwargs=dump_kwargs)
    # This serialized trigger is a read-only field for either the default or
    # custom trigger.
    serialized_trigger = JSONField(blank=True, default=dict, dump_kwargs=dump_kwargs)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user', 'action']
        unique_together = ("user", "action")
        verbose_name = "User Action"
        verbose_name_plural = "User Actions"

    def _serialize_action(self):
        if self.action:
            from ..serializers.v1 import ActionSerializer
            self.serialized_action = ActionSerializer(self.action).data

    def _serialize_behavior(self):
        if self.user_behavior and self.user_behavior.behavior:
            from ..serializers.v1 import BehaviorSerializer
            behavior = self.user_behavior.behavior
            self.serialized_behavior = BehaviorSerializer(behavior).data

    def _serialize_custom_trigger(self):
        if self.custom_trigger:
            from ..serializers.v1 import CustomTriggerSerializer
            self.serialized_custom_trigger = CustomTriggerSerializer(self.custom_trigger).data
        else:
            self.serialized_custom_trigger = None

    def _serialize_primary_goal(self):
        from ..serializers.simple import SimpleGoalSerializer
        pg = self.get_primary_goal()
        if pg:
            self.serialized_primary_goal = SimpleGoalSerializer(pg, user=self.user).data

    def _serialize_primary_category(self):
        cat = self.get_primary_category()
        if cat:
            from ..serializers.simple import SimpleCategorySerializer
            self.serialized_primary_category = SimpleCategorySerializer(cat).data

    def _serialize_trigger(self):
        # XXX call this *after* _serialize_custom_trigger
        # This a read-only field for triggers. If the user has a custom trigger,
        # that value gets added hear, otherwise this contains the serialized
        # default trigger.
        if self.serialized_custom_trigger:
            self.serialized_trigger = self.serialized_custom_trigger  # Yeah, just a copy :(
        elif self.default_trigger:
            from ..serializers.v1 import CustomTriggerSerializer
            self.serialized_trigger = CustomTriggerSerializer(self.default_trigger).data

    def __str__(self):
        return "{0}".format(self.action.title)

    def _completed(self, state):
        """Return the UserCompletedAction objects for this UserAction."""
        return self.usercompletedaction_set.filter(state=state)

    @property
    def num_completed(self):
        from .progress import UserCompletedAction
        return self._completed(UserCompletedAction.COMPLETED).count()

    @property
    def num_uncompleted(self):
        from .progress import UserCompletedAction
        return self._completed(UserCompletedAction.UNCOMPLETED).count()

    @property
    def num_snoozed(self):
        from .progress import UserCompletedAction
        return self._completed(UserCompletedAction.SNOOZED).count()

    @property
    def num_dismissed(self):
        from .progress import UserCompletedAction
        return self._completed(UserCompletedAction.DISMISSED).count()

    @property
    def trigger(self):
        if self.custom_trigger_id or self.custom_trigger:
            return self.custom_trigger
        return self.default_trigger

    @property
    def next_reminder(self):
        """Returns next_trigger_date in the user's local timezone."""
        if self.next_trigger_date is not None:
            return to_localtime(self.next_trigger_date, self.user)
        return self.next()

    def next(self):
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

    def _set_next_trigger_date(self):
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
            # try to back-fill (generate it) using the recurrence, but not
            # for relative reminders
            trigger = self.trigger
            if self.prev_trigger_date is None and trigger and not trigger.is_relative:
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

    def save(self, *args, **kwargs):
        """Adds a hook to update the prev_trigger_date & next_trigger_date
        whenever this object is saved. You can control this with the following
        additional keyword argument:

        * update_triggers: (default is True).

        """
        self._serialize_action()
        self._serialize_behavior()
        self._serialize_primary_goal()
        self._serialize_primary_category()
        self._serialize_custom_trigger()
        self._serialize_trigger()  # Keep *after* custom_trigger
        if kwargs.pop("update_triggers", True):
            self._set_next_trigger_date()
        return super().save(*args, **kwargs)

    @property
    def user_behavior(self):
        """Return the `UserBehavior` object that is related to the Action's
        parent Behavior.

        Returns a UserBehavior instance or None.

        """
        qs = UserBehavior.objects.select_related('behavior')
        qs = qs.prefetch_related('behavior__goals')
        return qs.filter(user=self.user, behavior=self.action.behavior).first()

    def get_notification_title(self):
        """Return the string to be used in this user's notification title."""
        goal = self.get_primary_goal() or Goal(title='')
        return self.action.get_notification_title(goal)

    def get_notification_text(self):
        """Return the string to be used in this user's notification text."""
        return self.action.get_notification_text()

    def get_user_goals(self):
        """Returns a QuerySet of published Goals related to this Action (and
        it's parent Behavior), but restricts those goals to those which the
        user has selected."""
        user_behavior = self.user_behavior
        if user_behavior:
            return user_behavior.get_user_goals()
        return Goal.objects.none()

    def get_primary_goal(self):
        """Return a Goal (or None) representing the primary goal associated
        with this user's selected Action."""
        if self.primary_goal:
            result = self.primary_goal
        else:
            result = self.get_user_goals().first()
        if not result and self.user_behavior:
            # Somehow, this user has no goals selected for this Action/Behavior,
            # so fall back to the first goal on the parent behavior.
            result = self.user_behavior.behavior.goals.first()
        return result

    def get_primary_category(self):
        """Return a Category (or None) representing the primary category
        associated with this user's selected Action."""
        if self.primary_category:
            return self.primary_category

        category = None
        goal = self.get_primary_goal()
        if goal:
            uc = UserCategory.objects.filter(
                category__in=goal.categories.all(),
                user=self.user
            ).first()
            if uc:
                category = uc.category
        if category is None:
            goal = self.action.behavior.goals.first()
            if goal:
                category = goal.categories.first()
        self.primary_category = category  # Save this locally
        return category

    @property
    def completed_today(self):
        """Return True if this action was completed today, False otherwise"""
        return self.user.usercompletedaction_set.filter(
            action=self.action,
            updated_on__range=local_day_range(self.user),
            state='completed'
        ).exists()

    @property
    def custom_triggers_allowed(self):
        """Check to see if the user/behavior is the child of a goal within a
        Package where custom triggers are restricted. """
        return _custom_triggers_allowed(self.user, self)

    @property
    def default_trigger(self):
        if not hasattr(self, "_default_trigger"):
            self._default_trigger = self.action.default_trigger
        return self._default_trigger

    def get_custom_trigger_name(self):
        """This should generate a unique name for this object's custom
        trigger."""
        return "custom trigger for useraction-{0}".format(self.id)

    def queued_notifications(self):
        ct = ContentType.objects.get_by_natural_key('goals', 'action')
        msgs = self.user.gcmmessage_set.filter(
            content_type=ct,
            object_id=self.action.id
        )
        msgs = msgs.order_by('-deliver_on').distinct()
        return msgs

    objects = UserActionManager()
