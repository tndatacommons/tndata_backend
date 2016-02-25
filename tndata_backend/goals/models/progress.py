"""
"""
from django.conf import settings
from django.db import models
from django.db.models import Min
from jsonfield import JSONField

from .public import Action
from .users import UserAction
from ..managers import DailyProgressManager

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


class DailyProgress(models.Model):
    """This model aggregates some information about the user's daily progress
    toward adopting behaviors (or achieving a goal).

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

    # Aggregate Behavior Data
    behaviors_total = models.IntegerField(
        default=0,
        help_text="Total number of behaviors selected on this day"
    )
    # The Behaviors Status is a dict for storing info about the user's progress
    # toward a behavior (i.e. what class of notifications/actions should they
    # receive). Each entry is a key of `behavior-<id>` with a `status` value.
    #
    #   behavior-<id>: <status>
    #
    behaviors_status = JSONField(
        blank=True,
        default=dict,
        help_text="Describes the user's status on work toward this behavior"
    )

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

    def set_status(self, behavior, status):
        key = 'behavior-{}'.format(behavior.id)
        self.behaviors_status[key] = status

    def get_status(self, behavior):
        key = 'behavior-{}'.format(behavior.id)
        return self.behaviors_status[key]

    def _update_useraction_stats(self):
        start, end = local_day_range(self.user, dt=self.created_on)
        from_date = self.user.useraction_set.aggregate(Min('created_on'))
        from_date = from_date['created_on__min'] or start

        # Count the UserActions selected.
        self.actions_total = self.user.useraction_set.filter(
            created_on__range=(from_date, end)).count()

        # count the stats for UserCompletedActions
        ucas = self.user.usercompletedaction_set.filter(
            created_on__range=(from_date, end))
        self.actions_completed = ucas.filter(
            state=UserCompletedAction.COMPLETED).count()
        self.actions_snoozed = ucas.filter(
            state=UserCompletedAction.SNOOZED).count()
        self.actions_dismissed = ucas.filter(
            state=UserCompletedAction.DISMISSED).count()

    def _update_userbehavior_stats(self):
        start, end = local_day_range(self.user, dt=self.created_on)
        from_date = self.user.userbehavior_set.aggregate(Min('created_on'))
        from_date = from_date['created_on__min'] or start

        # Count the UserBehaviors selected
        self.behaviors_total = self.user.userbehavior_set.filter(
            created_on__range=(from_date, end)).count()

    def _update_customaction_stats(self):
        start, end = local_day_range(self.user, dt=self.created_on)
        from_date = self.user.customaction_set.aggregate(Min('created_on'))
        from_date = from_date['created_on__min'] or start

        # Check on number of CustomAction objects we have today.
        self.customactions_total = self.user.customaction_set.filter(
            created_on__range=(from_date, end)).count()

        # Count status of UserCompletedAction data for today
        uccas = self.user.usercompletedcustomaction_set.filter(
            created_on__range=(from_date, end)
        )
        self.customactions_completed = uccas.filter(
            state=UserCompletedAction.COMPLETED).count()
        self.customactions_snoozed = uccas.filter(
            state=UserCompletedAction.SNOOZED).count()
        self.customactions_dismissed = uccas.filter(
            state=UserCompletedAction.DISMISSED).count()

    def update_stats(self):
        self._update_userbehavior_stats()
        self._update_useraction_stats()
        self._update_customaction_stats()

    # The DailyProgress manager has custom convenience methods:
    # - for_user(user) -- Gets or creates an instance for "today"
    objects = DailyProgressManager()
