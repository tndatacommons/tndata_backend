"""
Mappings between users and their selected public content.

    [Category] <-> [Goal] <-> [Behavior] <- [Action]
        |            |            |            |
  [UserCategory] [UserGoal]  [UserBehavior] [UserAction]
        \            \            /            /
         \            \          /            /

                        [ User ]

"""
import django.dispatch
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from utils.user_utils import local_day_range, to_localtime, to_utc
from notifications.models import GCMMessage

from .misc import _custom_triggers_allowed
from .public import Action, Behavior, Category, Goal
from .triggers import Trigger
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
    updated_on = models.DateTimeField(auto_now=True)

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

    # Goal-related app engagment numbers. Similar to values on the DailyProgress
    engagement_15_days = models.FloatField(default=0, blank=True)
    engagement_30_days = models.FloatField(default=0, blank=True)
    engagement_60_days = models.FloatField(default=0, blank=True)

    # NOTE: See UserGoal.objects.engagement_rank
    # This value is periodically updated by a management command.
    engagement_rank = models.FloatField(default=0, blank=True)

    completed = models.BooleanField(default=False)
    completed_on = models.DateTimeField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user', 'goal']
        unique_together = ("user", "goal")
        verbose_name = "User Goal"
        verbose_name_plural = "User Goals"

    def __str__(self):
        return "{0}".format(self.goal.title)

    def calculate_engagement(self, days=15):
        result = None
        if days in [15, 30, 60]:
            result = self.user.usercompletedaction_set.engagement(
                user=self.user, goal=self.goal, days=days
            )
        if result and days == 15:
            self.engagement_15_days = result
        elif result and days == 30:
            self.engagement_30_days = result
        elif result and days == 60:
            self.engagement_60_days = result

    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)
        self.get_primary_category()  # will actually set the primary category.
        return result

    def weekly_completions(self):
        """The number of Actions / CustomActions that the user has completed
        in the past 7 days within this goal"""
        uccas = self.user.usercompletedcustomaction_set.filter(
            state='completed', customaction__goal=self.goal).distinct().count()
        ucas = self.user.usercompletedaction_set.filter(
            state='completed',
            useraction__primary_goal=self.goal).distinct().count()
        return uccas + ucas

    def complete(self):
        """Mark this goal as complete"""
        self.completed = True
        self.completed_on = timezone.now()

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

    def add_behaviors(self, behaviors=None, create_actions=True):
        """Create UserBehavior instances for all of the published Behaviors
        within the associated Goal. This method will not create duplicate
        instances of UserBehavior.

        - behaviors: Only create UserBehavior objects for the Behaviors in the
          provided list (this should be a list of Behavior objects)
        - create_actions: If True, this method will also create UserActions
          for all of the published Actions beneath the Behavior.

        """
        if behaviors is None:
            behaviors = Behavior.objects.published()

        for behavior in behaviors:
            UserBehavior.objects.update_or_create(
                user=self.user,
                behavior=behavior,
            )
            if create_actions:
                for action in behavior.action_set.published():
                    UserAction.objects.update_or_create(
                        user=self.user,
                        action=action,
                        primary_goal=self.goal,
                        primary_category=self.get_primary_category()
                    )

    objects = UserGoalManager()


# -----------------------------------------------------------------------------
#
# A signal that will be fired when a UserBehavior is "completed", meaning that
# the user has completed all of the actions within the related Behavior.
#
# The provided arguments include:
#
# - sender: the UserBehavior class
# - instance: the instance of the UserBehavior class.
#
# -----------------------------------------------------------------------------
userbehavior_completed = django.dispatch.Signal(providing_args=['instance'])


class UserBehavior(models.Model):
    """A Mapping between Users and the Behaviors they've selected.

    - notifications for this are scheduled by the `create_notifications`
      management command.
    - As of the API version 2, when a user selects a behavior (i.e. an instance
      of UserBehavior is created), we also create UserAction objects for all
      of the Behavior's child Actions.

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
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{0}".format(self.behavior.title)

    class Meta:
        ordering = ['user', 'behavior']
        unique_together = ("user", "behavior")
        verbose_name = "User Behavior"
        verbose_name_plural = "User Behaviors"

    def complete(self):
        """Mark this behavior as complete, and fire a signal to notify the
        user's selected goals that are parents of this behavior.
        """
        self.completed = True
        self.completed_on = timezone.now()
        self.save()  # WE MUST save this prior to firing the signal.
        # fire a signal
        userbehavior_completed.send(
            sender=self.__class__,
            instance=self,
        )

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

    def add_actions(self, primary_category=None, primary_goal=None, action_id=None):
        """Create UserAction instances for all of the published Actions within
        the associated behavior. This method will not create duplicate instances
        of UserAction.

        - primary_category: If specified, will be set as the UserAction's
          primary_category field. If omitted, this value is looked up.
        - primary_goal: If specified, will be set as the UserAction's
          primary_goal field. If omitted, this value is looked up.
        - action_id: If specified, we only create a UserAction whose action
          field matches the given value (e.g. if we only want to add a single
          action).

        """

        defaults = {
            'primary_goal': primary_goal,
            'primary_category': primary_category
        }
        if primary_goal is None:
            defaults['primary_goal'] = self.get_user_goals().first()
        if primary_category is None:
            defaults['primary_category'] = self.get_user_categories().first()

        if action_id:
            # Note: may not be saved as "published", yet, but that's OK
            actions = Action.objects.filter(id=action_id)
        else:
            actions = Action.objects.published(behavior=self.behavior)

        for action in actions:
            UserAction.objects.update_or_create(
                user=self.user,
                action=action,
                defaults=defaults
            )

    objects = UserBehaviorManager()


class UserAction(models.Model):
    """A Mapping between Users and the Actions they've selected. This model
    essentially encapusaltes information about a notification we send to the
    user.

    - Notifications == Actions (which are public and selectable by anyone)
    - Notifications are scheduled by the `create_notifications` management
      command.
    - Data and dates are generated by this object's Trigger
    - Once users receive a notification, any feedback they give goes in a
      UserCompletedAction instance.

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

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user', 'next_trigger_date', 'action']
        unique_together = ("user", "action")
        verbose_name = "User Action"
        verbose_name_plural = "User Actions"

    def __str__(self):
        return "{0}".format(self.action.title)

    def _completed(self, state):
        """Return the UserCompletedAction objects for this UserAction."""
        return self.usercompletedaction_set.filter(state=state)

    @property
    def priority(self):
        """Returns a string representation of the object's priority, suitable
        for sending a message via GCM.

        ----

        doh. GCMMessage objects expect a string 'low', 'medium', 'high',
        while I've built Actions with an integer priority :-/
        """
        # Action (int) --> GCMMessage (string)
        priorities = {
            Action.LOW: GCMMessage.LOW,
            Action.MEDIUM: GCMMessage.MEDIUM,
            Action.HIGH: GCMMessage.HIGH
        }

        # Ensure that custom triggers get set with HIGH priority
        if self.custom_trigger is not None:
            return priorities.get(Action.HIGH)

        return priorities.get(self.action.priority, GCMMessage.LOW)

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

    @property
    def next_in_sequence(self):
        """Is this action the next in sequence. Returns True or False."""
        return self.id in self.user.useraction_set.next_in_sequence(
            [self.action.behavior],
            published=True
        ).values_list("pk", flat=True)

    def next(self):
        """Return the next trigger datetime object in the user's local timezone
        or None. This method will either return the value of `next_trigger_date`
        or the next date/time generated from the trigger, whichever is *next*."""

        now = timezone.now()
        trigger_times = []
        trigger = self.trigger
        is_dynamic = trigger and trigger.is_dynamic
        is_custom = bool(self.custom_trigger)

        # IF we have a custom trigger, a recurring trigger OR if this Action is
        # the next in a sequence, then we'll proceed with generating the
        # appropriate time. Otherwise, we'll short-circuit this method.
        if trigger and not is_custom and not any([
            trigger.serialized_recurrences(),
            self.next_in_sequence
        ]):
            return None

        # If we have a dynamic trigger, let's first determine wether or not
        # we need to re-generate a time; i.e. if the next_trigger_date is in
        # the past.
        if is_dynamic and self.next_trigger_date is None:
            trigger_times.append(trigger.next(user=self.user))
        elif is_dynamic and self.next_trigger_date < now:
            trigger_times.append(trigger.next(user=self.user))
        elif self.next_trigger_date and self.next_trigger_date > now:
            # Check to see if we can re-use the existing trigger date,
            # converting it back to the users local timezone
            trigger_times.append(to_localtime(self.next_trigger_date, self.user))

        # For all non-dynamic triggers, we just regenerate a time.
        if trigger and not is_dynamic:
            trigger_times.append(trigger.next(user=self.user))

        # Pick the "next up" trigger from our list of possibilities.
        try:
            return min(filter(None, trigger_times))
        except ValueError:
            pass  # we probably tried to pick the min from an empty list.

        return None

    def _set_next_trigger_date(self):
        """Attempt to  stash this action's next trigger date so we can query
        for it. This first tries any custom triggers then uses the default
        trigger. The result may be None (it's possible some action's no longer
        have a future trigger).

        NOTE: Always store this in UTC.

        """
        # ---------------------------------------------------------------------
        # Actions/Notifications should be queued up based on their sequence. So,
        # unless this action is next in sequence for the user, we don't want to
        # generate a next trigger date...
        #
        # UNLESS, the trigger has a recurrence.
        # ---------------------------------------------------------------------
        trigger = self.trigger
        if trigger and (self.next_in_sequence or trigger.serialized_recurrences):
            # This trigger retuns the date in the user's timezone, so convert
            # it back to UTC.
            next_date = to_utc(self.next())

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
        return self.next_trigger_date

    def save(self, *args, **kwargs):
        """Adds a hook to update the prev_trigger_date & next_trigger_date
        whenever this object is saved. You can control this with the following
        additional keyword argument:

        * update_triggers: (default is True).

        """
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

    @property
    def userbehavior_id(self):
        """Return the UserBehavior ID for the related Action's Behavior."""
        try:
            userbehavior = UserBehavior.objects.get(
                user__id=self.user_id,
                behavior__action__id=self.action_id
            )
            return userbehavior.id
        except UserBehavior.DoesNotExist:
            return None

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

    @property
    def goal_title(self):
        """Return the title string for this object's primary goal."""
        return self.get_primary_goal(only='title').title

    @property
    def goal_description(self):
        """Return the description string for this object's primary goal."""
        return self.get_primary_goal(only='description').description

    @property
    def goal_icon(self):
        """Return the description string for this object's primary goal."""
        if self.primary_goal_id:
            return self.primary_goal.get_absolute_icon()
        return None

    def get_primary_usergoal(self, only=None):
        """Return a UserGoal object for this instance's `primary_goal`."""
        result = None
        if self.primary_goal_id:
            result = self.user.usergoal_set.filter(goal__id=self.primary_goal_id)
            if only:
                result = result.only(only)
            result = result.first()
        return result

    def get_primary_goal(self, only=None):
        """Return a Goal (or None) representing the primary goal associated
        with this user's selected Action."""
        if self.primary_goal:
            result = self.primary_goal
        elif only:
            result = self.get_user_goals().only(only).first()
        else:
            result = self.get_user_goals().first()

        # Somehow, this user has no goals selected for this Action/Behavior,
        # so fall back to the first goal on the parent behavior.
        if not result and self.user_behavior and only:
            result = self.user_behavior.behavior.goals.only(only).first()
        elif not result and self.user_behavior:
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
    def completed(self):
        return self.user.usercompletedaction_set.filter(
            action=self.action,
            useraction=self,
            state='completed'
        ).exists()

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

    def enable_trigger(self):
        """If the user has a custom trigger, this method will ensure it
        is enabled."""
        if self.custom_trigger:
            self.custom_trigger.disabled = False
            self.custom_trigger.save()

    def disable_trigger(self):
        """Disables the trigger for this action."""
        if self.custom_trigger:
            self.custom_trigger.disabled = True
            self.custom_trigger.save()
        elif self.default_trigger:
            # Create a custom trigger that's a duplicate and disable it.
            self.custom_trigger = Trigger.objects.create(
                user=self.user,
                name=self.get_custom_trigger_name(),
                time_of_day=self.default_trigger.time_of_day,
                frequency=self.default_trigger.frequency,
                time=self.default_trigger.time,
                trigger_date=self.default_trigger.trigger_date,
                recurrences=self.default_trigger.recurrences,
                start_when_selected=self.default_trigger.start_when_selected,
                stop_on_complete=self.default_trigger.stop_on_complete,
                disabled=True,
                relative_value=self.default_trigger.relative_value,
                relative_units=self.default_trigger.relative_units,
            )

    objects = UserActionManager()
