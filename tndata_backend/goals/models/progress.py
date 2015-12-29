"""
"""
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Avg, Sum
from django.utils import timezone

from utils import dateutils
from utils.user_utils import local_day_range


from .public import Action, Category, Goal
from .users import UserAction, UserBehavior, UserCategory, UserGoal


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


class BehaviorProgress(models.Model):
    """Encapsulates a user's progress & history toward certain behaviors.

    The following are aggregates for a user's progress on Actions within this
    Behavior. They're populated via the `aggregate_progress` management command.

    * daily_actions_total
    * daily_actions_completed
    * daily_action_progress

    NOTE: The OFF_COURSE, SEEKING, and ON_COURSE values have essentially been
    depricated, so this model really only aggregates up completed action
    values at the moment.

    TODO: Remove these ^ old fields.

    """
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

    # Status is for user-input feedback (e.g. the daily check-in)
    status = models.IntegerField(choices=PROGRESS_CHOICES)

    # Action progress is calculated based on completed vs. non-completed Actions
    daily_actions_total = models.IntegerField(default=0)
    daily_actions_completed = models.IntegerField(default=0)
    daily_action_progress = models.FloatField(default=0)

    reported_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reported_on']
        get_latest_by = "reported_on"
        verbose_name = "Behavior Progress"
        verbose_name_plural = "Behavior Progresses"

    def __str__(self):
        return self.get_status_display()

    def _calculate_action_progress(self):
        """Count the user's scheduled + completed actions that are children of
        the related UserBehavior.behavior, but only do this for the date this
        progress item was saved (so we can back-fill old action progress if
        available).

        This method will overwrite the following fields:

        - daily_actions_total
        - daily_actions_completed
        - daily_action_progress

        """
        date_range = local_day_range(self.user, self.reported_on)

        # NOTE: UserAction.next_trigger_date gets updated daily, so we can't
        # use it to query for historical data. Intead, we need to look at the
        # history of completed information (UserCompletedAction objects where
        # the action's parent behavior matches this behavior).
        ucas = self.user.usercompletedaction_set.filter(
            user=self.user,
            action__behavior=self.user_behavior.behavior,
            updated_on__range=date_range
        )
        self.daily_actions_total = ucas.count()
        self.daily_actions_completed = ucas.filter(
            state=UserCompletedAction.COMPLETED
        ).count()

        if self.daily_actions_total > 0:
            self.daily_action_progress = (
                self.daily_actions_completed / self.daily_actions_total
            )

    def save(self, *args, **kwargs):
        self._calculate_action_progress()
        super().save(*args, **kwargs)

    @property
    def daily_action_progress_percent(self):
        """The `daily_action_progress` value as integer percent."""
        return int(self.daily_action_progress * 100)

    @property
    def status_display(self):
        return self.get_status_display()

    @property
    def behavior(self):
        return self.user_behavior.behavior


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
    """Aggregates data from `BehaviorProgress` up to 'today'.

    The following fields are used to aggregate a user's completed v. incomplete
    Actions withing this goal (and it's child behaviors):

    * daily_actions_total
    * daily_action_completed
    * daily_action_progress
    * weekly_actions_total
    * weekly_actions_completed
    * weekly_action_progress
    * actions_total
    * actions_completed
    * action_progress

    The following fields store the user's end-of-day "How are doing" data
    related to the selected goal. This daily check-in value gets averaged over
    the past 7 and 30 days (weekly, monthly)

    * daily_checkin
    * weekly_checkin
    * monthly_checkin

    The following fields were used to aggregate the now-deprecated
    BehaviorProgress data up to the goal.

    * current_score
    * current_total
    * max_total

    TODO: ^ remove these fields and associated code?

    ----

    NOTE: These values are populated via the `aggregate_progress` command.

    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    goal = models.ForeignKey(Goal)
    usergoal = models.ForeignKey(UserGoal, null=True)

    # Aggregating the self-reported Behavior Progress
    current_score = models.FloatField(default=0)
    current_total = models.FloatField(default=0)
    max_total = models.FloatField(default=0)

    # Daily check-in fields, for a user's "How are you doing on this Goal"
    # data. Weekly and Monthly values are averages over the past 7 and 30 days.
    daily_checkin = models.IntegerField(default=0)
    weekly_checkin = models.FloatField(default=0)
    monthly_checkin = models.FloatField(default=0)

    # Aggregating the user's completed Actions for the day
    daily_actions_total = models.IntegerField(default=0)
    daily_actions_completed = models.IntegerField(default=0)
    daily_action_progress = models.FloatField(default=0)

    # Weekly aggregation for the user's completed Actions
    weekly_actions_total = models.IntegerField(default=0)
    weekly_actions_completed = models.IntegerField(default=0)
    weekly_action_progress = models.FloatField(default=0)

    # Historical aggregations of the user's completed actions. See the
    # PROGRESS_HISTORY_DAYS settings.
    actions_total = models.IntegerField(default=0)
    actions_completed = models.IntegerField(default=0)
    action_progress = models.FloatField(default=0)

    reported_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'goal', 'reported_on')
        ordering = ['-reported_on']
        get_latest_by = "reported_on"
        verbose_name = "Goal Progress"
        verbose_name_plural = "Goal Progresses"

    def __str__(self):
        return "{}".format(self.current_score)

    @property
    def daily_action_progress_percent(self):
        """The `daily_action_progress` value as integer percent."""
        return int(self.daily_action_progress * 100)

    @property
    def weekly_action_progress_percent(self):
        """The `weekly_action_progress` value as integer percent."""
        return int(self.weekly_action_progress * 100)

    @property
    def action_progress_percent(self):
        """The `action_progress` value as integer percent."""
        return int(self.action_progress * 100)

    def child_behaviorprogresses(self):
        """Returns a queryset of BehaviorProgress instances whose related
        Behavior is a child of this object's Goal.

        """
        lookup = {'user_behavior__behavior__goals__in': [self.goal]}
        return self.user.behaviorprogress_set.filter(**lookup)

    def _calculate_actions_stats(self, days=1):
        """Calculate the actions stats from the BehaviorProgress model over
        some time period ending with either this model's reported_on date or
        today's date if if `reported_on` is None.

        Returns a 3-tuple of the following: (completed, total, progress), where

        * completed - the number of actions completed
        * total - the total number of actions scheduled
        * progress - the percentage (as a float): completed / total

        """
        start, end = local_day_range(self.user, self.reported_on)
        start = start - timedelta(days=days)

        # Run the aggregate over the relevant BehaviorProgress objects.
        qs = self.child_behaviorprogresses().filter(reported_on__range=(start, end))
        qs = qs.aggregate(Sum('daily_actions_total'), Sum('daily_actions_completed'))

        total = qs.get('daily_actions_total__sum', 0) or 0
        completed = qs.get('daily_actions_completed__sum', 0) or 0
        progress = 0
        if total > 0:
            progress = completed / total
        return (completed, total, progress)

    def calculate_daily_action_stats(self):
        """Aggregate the BehaviorProgress action status saved on the same day."""
        completed, total, progress = self._calculate_actions_stats(days=1)
        self.daily_actions_completed = completed
        self.daily_actions_total = total
        self.daily_action_progress = progress

    def calculate_weekly_action_stats(self):
        """Aggregate the BehaviorProgress action stats for the past week."""
        completed, total, progress = self._calculate_actions_stats(days=7)
        self.weekly_actions_completed = completed
        self.weekly_actions_total = total
        self.weekly_action_progress = progress

    def calculate_aggregate_action_stats(self):
        """Aggregate the BehaviorProgress action stats."""
        completed, total, progress = self._calculate_actions_stats(
            days=settings.PROGRESS_HISTORY_DAYS
        )
        self.actions_completed = completed
        self.actions_total = total
        self.action_progress = progress

    def _calculate_score(self, digits=2):
        v = 0
        if self.max_total > 0:
            v = round(self.current_total / self.max_total, digits)
        self.current_score = v

    def recalculate_score(self):
        """Recalculate all of the BehaviorProgress values for the current date,
        updating the relevant score-related fields."""
        start = self.reported_on.replace(hour=0, minute=0, second=0, microsecond=0)
        end = self.reported_on.replace(hour=23, minute=59, second=59, microsecond=999999)

        scores = self.child_behaviorprogresses()
        scores = scores.filter(reported_on__range=(start, end))
        scores = scores.values_list('status', flat=True)

        self.current_total = sum(scores)
        self.max_total = len(scores) * BehaviorProgress.ON_COURSE
        self._calculate_score()

    def _calculate_checkin_average(self, days):
        report_date = self.reported_on if self.reported_on else timezone.now()
        from_date = report_date - timedelta(days=days)
        to_date = self.reported_on
        result = GoalProgress.objects.filter(
            user=self.user,
            goal=self.goal,
            usergoal=self.usergoal,
            reported_on__range=(from_date, to_date)
        ).aggregate(Avg('daily_checkin'))
        return result.get('daily_checkin__avg', 0) or 0

    def _weekly_checkin_average(self):
        self.weekly_checkin = self._calculate_checkin_average(7)

    def _monthly_checkin_average(self):
        self.monthly_checkin = self._calculate_checkin_average(30)

    def save(self, *args, **kwargs):
        # Aggregate Behavior scores
        self._calculate_score()

        # Action-related stats
        self.calculate_daily_action_stats()
        self.calculate_weekly_action_stats()
        self.calculate_aggregate_action_stats()

        # Daily "how am i doing" stats and averages.
        self._weekly_checkin_average()
        self._monthly_checkin_average()
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
        verbose_name_plural = "Category Progresses"

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
