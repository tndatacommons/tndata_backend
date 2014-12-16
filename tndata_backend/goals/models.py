from django.conf import settings
from django.db import models
from djorm_pgarray import fields as pg_fields


class Goal(models.Model):
    """Essentially a *category* for user behavior actions."""
    rank = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=128, db_index=True)
    explanation = models.TextField()
    max_neef_tags = pg_fields.TextArrayField()
    sdt_major = models.CharField(max_length=128)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['rank', 'name']
        verbose_name = "Goal"
        verbose_name_plural = "Goals"


class Behavior(models.Model):
    """Users see 'I want to...' and these populate the options. Also a Grouping
    of behavior steps/recipes."""
    goal = models.ForeignKey(Goal)
    name = models.CharField(max_length=128, db_index=True)
    summary = models.TextField()
    description = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['goal', 'name']
        verbose_name = 'Behavior'
        verbose_name_plural = 'Behaviors'


class BehaviorStep(models.Model):
    REMINDER_TYPE_CHOICES = (
        ('temporal', 'Temporal'),
        ('geolocation', 'Geolocation')
    )
    REPEAT_CHOICES = (
        ('daily', 'Every Day'),
        ('weekly', 'Every Week'),
        ('monthly', 'Every Month'),
        ('yearly', 'Every Year'),
    )
    goal = models.ForeignKey(Goal)
    behavior = models.ForeignKey(Behavior)
    name = models.CharField(max_length=128, db_index=True)
    description = models.TextField()
    reminder_type = models.CharField(max_length=32, choices=REMINDER_TYPE_CHOICES, blank=True)
    default_time = models.TimeField(blank=True, null=True)
    default_repeat = models.CharField(max_length=32, blank=True, choices=REPEAT_CHOICES)
    default_location = models.CharField(max_length=32, blank=True)  # TODO: GIS?

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'Behavior Step'
        verbose_name_plural = 'Behavior Steps'

    def reminder(self, user):
        """Get reminder info for a given user. Returns a tuple of:

            (type, time, repeat, location)

        """
        reminder_data = self.get_custom_reminder(user)
        if reminder_data is None:
            reminder_data = (
                self.reminder_type,
                self.default_time,
                self.default_repeat,
                self.default_location
            )
        return reminder_data

    def get_custom_reminder(self, user):
        try:
            cr = CustomReminder.objects.get(user=user, behavior_step=self)
            return (cr.reminder_type, cr.time, cr.repeat, cr.location)
        except CustomReminder.DoesNotExist:
            return None


class CustomReminder(models.Model):
    """A User's custom reminder for a `BehaviorStep`."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    behavior_step = models.ForeignKey(BehaviorStep)
    reminder_type = models.CharField(
        max_length=32,
        blank=True,
        choices=BehaviorStep.REMINDER_TYPE_CHOICES
    )
    time = models.TimeField(blank=True, null=True)
    repeat = models.CharField(
        max_length=32,
        blank=True,
        choices=BehaviorStep.REPEAT_CHOICES
    )
    location = models.CharField(max_length=32, blank=True)  # TODO: GIS?

    def __str__(self):
        return 'Custom Reminder for {0}'.format(self.behavior_step)

    class Meta:
        ordering = ['behavior_step']
        unique_together = ('user', 'behavior_step')
        verbose_name = 'Custom Reminder'
        verbose_name_plural = 'Custom Reminders'


class ChosenBehavior(models.Model):
    """Records an User's Goal/Behavior Choices."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    goal = models.ForeignKey(Goal)
    behavior = models.ForeignKey(Behavior)
    date_selected = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return "{0} selected on {1}".format(self.behavior, self.date_selected)

    class Meta:
        ordering = ['date_selected']
        verbose_name = 'Chosen Behavior'
        verbose_name_plural = 'Chosen Behaviors'


class CompletedBehaviorStep(models.Model):
    """When a user _completes_ some behavior step."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    goal = models.ForeignKey(Goal)
    behavior = models.ForeignKey(Behavior)
    behavior_step = models.ForeignKey(BehaviorStep)
    date_completed = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return "{0} completed on {1}".format(self.behavior_step, self.date_completed)

    class Meta:
        ordering = ['date_completed']
        verbose_name = 'Chosen Behavior Step'
        verbose_name_plural = 'Chosen Behavior Steps'
