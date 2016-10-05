"""
"""
from django.conf import settings
from django.db import models
from django.db.models import Min
from jsonfield import JSONField

from .public import Action
from .users import UserAction
from ..managers import DailyProgressManager, UserCompletedActionManager

from utils.user_utils import local_day_range


class UserCompletedAction(models.Model):
    """Users can tell us they "completed" an Action. This is represented in
    the mobile app by a 'I did it' button.

    Note that there may be many instances of this model for a user/action, and
    that an aggregate of these tells us how often a user performs (or says they
    perform) this action.

    """
    UNCOMPLETED = 'uncompleted'
    COMPLETED = 'completed'
    DISMISSED = 'dismissed'
    SNOOZED = 'snoozed'
    UNSET = '-'

    STATE_CHOICES = (
        (UNCOMPLETED, 'Uncompleted'),
        (COMPLETED, 'Completed'),
        (DISMISSED, 'Dismissed'),
        (SNOOZED, 'Snoozed'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    useraction = models.ForeignKey(UserAction)
    action = models.ForeignKey(Action)

    # NOTE: See the `action_completed` signal handler (in models.signals)
    state = models.CharField(
        max_length=32,
        default=UNSET,
        choices=STATE_CHOICES
    )

    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{0}".format(self.action.title)

    class Meta:
        ordering = ['-updated_on', 'user', 'action']
        verbose_name = "User Completed Action"
        verbose_name_plural = "User Completed Action"
        get_latest_by = 'updated_on'

    @property
    def uncompleted(self):
        return self.state == self.UNCOMPLETED

    @property
    def completed(self):
        return self.state == self.COMPLETED

    @property
    def dismissed(self):
        return self.state == "dismissed"

    @property
    def snoozed(self):
        return self.state == "snoozed"

    @property
    def usergoal(self):
        ug = self.user.usergoal_set.filter(goal=self.useraction.primary_goal)
        return ug.first()

    def sibling_actions_completed(self):
        """Query to see if sibling actions (those under the same primary goal)
        have been completed.

        Returns True if all the actions are completed, False otherwise.

        """
        # Note: this query is for UserActions under the same primary goal that
        # have not been completed. If this returns results, the sibling actions
        # have not been completed.
        goal = self.useraction.primary_goal
        if goal:
            return not UserAction.objects.filter(
                user=self.user,
                primary_goal=goal,
                usercompletedaction=None
            ).distinct().exists()
        return False

    objects = UserCompletedActionManager()


class DailyProgress(models.Model):
    """This model aggregates some information about the user's daily progress
    toward achieving a goal.

    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    # Aggregate Numbers for Actions. These are populated by inspecting the
    # UserCompletedAction entries for a user.
    actions_total = models.IntegerField(
        default=0,
        help_text="Total number of actions for the user on this day"
    )
    actions_completed = models.IntegerField(
        default=0,
        help_text="Number of actions the user completed"
    )
    actions_snoozed = models.IntegerField(
        default=0,
        help_text="Number of actions the user snoozed"
    )
    actions_dismissed = models.IntegerField(
        default=0,
        help_text="Number of actions the user dismissed"
    )

    # Aggregation Number for Custom Actions. These are populated by inspecting
    # the UserCompletedCustomAction entries for a user.
    customactions_total = models.IntegerField(
        default=0,
        help_text="Total number of custom actions for the user on this day"
    )
    customactions_completed = models.IntegerField(
        default=0,
        help_text="Number of custom actions the user completed"
    )
    customactions_snoozed = models.IntegerField(
        default=0,
        help_text="Number of custom actions the user snoozed"
    )
    customactions_dismissed = models.IntegerField(
        default=0,
        help_text="Number of custom actions the user dismissed"
    )

    # This is where we store the daily progress feedback for goals. It's a
    # dict of the form: {'goal-<id>': int_value}, where each value is the
    # user's self-reported feedback.
    goal_status = JSONField(
        blank=True,
        default=dict,
        help_text="User feedback on their progress toward achieving goals"
    )

    # NOTE: This value gets set by the `set_dp_checkin_streak` signal handler.
    checkin_streak = models.IntegerField(
        default=0,
        blank=True,
        help_text="A count of check-in streaks (how many days in a row a user "
                  "has submitted a daily check-in."
    )

    # App / Notification engagement
    # See: UserCompletedActionManager.engagement
    engagement_15_days = models.FloatField(default=0, blank=True)
    engagement_30_days = models.FloatField(default=0, blank=True)
    engagement_60_days = models.FloatField(default=0, blank=True)

    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{0}".format(self.user)

    class Meta:
        ordering = ['-updated_on', 'user']
        verbose_name = 'Daily Progress'
        verbose_name_plural = 'Daily Progresses'
        get_latest_by = 'updated_on'

    @property
    def behaviors_total(self):
        return 0

    @property
    def actions(self):
        """Return a dict of all action stats."""
        return {
            'total': self.actions_total,
            'snoozed': self.actions_snoozed,
            'completed': self.actions_completed,
            'dismissed': self.actions_dismissed,
        }

    @property
    def customactions(self):
        """Return a dict of all custom action stats."""
        return {
            'total': self.customactions_total,
            'snoozed': self.customactions_snoozed,
            'completed': self.customactions_completed,
            'dismissed': self.customactions_dismissed,
        }

    def set_goal_status(self, goal_id, value):
        if all([goal_id, value]):
            key = 'goal-{}'.format(goal_id)
            self.goal_status[key] = value
        return self.goal_status

    def _update_useraction_stats(self):
        start, end = local_day_range(self.user, dt=self.created_on)
        from_date = self.user.useraction_set.aggregate(Min('created_on'))
        from_date = from_date['created_on__min'] or start

        # Count the total number of UserActions selected (ever)
        self.actions_total = self.user.useraction_set.filter(
            created_on__range=(from_date, end)).count()

        # Count the stats for today's UserCompletedActions
        ucas = self.user.usercompletedaction_set.filter(
            created_on__range=(start, end))
        self.actions_completed = ucas.filter(
            state=UserCompletedAction.COMPLETED).count()
        self.actions_snoozed = ucas.filter(
            state=UserCompletedAction.SNOOZED).count()
        self.actions_dismissed = ucas.filter(
            state=UserCompletedAction.DISMISSED).count()

    def _update_customaction_stats(self):
        start, end = local_day_range(self.user, dt=self.created_on)
        from_date = self.user.customaction_set.aggregate(Min('created_on'))
        from_date = from_date['created_on__min'] or start

        # Count the total number of CustomAction objects (ever)
        self.customactions_total = self.user.customaction_set.filter(
            created_on__range=(from_date, end)).count()

        # Count status of UserCompletedAction data for today
        uccas = self.user.usercompletedcustomaction_set.filter(
            created_on__range=(start, end)
        )
        self.customactions_completed = uccas.filter(
            state=UserCompletedAction.COMPLETED).count()
        self.customactions_snoozed = uccas.filter(
            state=UserCompletedAction.SNOOZED).count()
        self.customactions_dismissed = uccas.filter(
            state=UserCompletedAction.DISMISSED).count()

    def update_stats(self):
        self._update_useraction_stats()
        self._update_customaction_stats()

    def usercompletedactions(self):
        """Return a queryset of UserCompletedAction objects that were updated
        during the same day that this instance was created.
        """
        day_range = local_day_range(self.user, dt=self.created_on)
        return self.user.usercompletedaction_set.filter(updated_on__range=day_range)

    def calculate_engagement(self, days=15):
        func = UserCompletedAction.objects.engagement
        if days == 15:
            self.engagement_15_days = func(self.user, days=days)
        elif days == 30:
            self.engagement_30_days = func(self.user, days=days)
        elif days == 60:
            self.engagement_60_days = func(self.user, days=days)

    # The DailyProgress manager has custom convenience methods:
    # - for_user(user) -- Gets or creates an instance for "today"
    objects = DailyProgressManager()
