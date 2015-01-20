"""
Models for the Goals app.

This is our collection of Goals. They're organized by category & interest;

    [Category] <-> [Interest] -> [Action]

A User chooses an Action as something they want to do or achieve (this is their
goal). Continued performance of that action constitutes a behavior or habit.

Actions are the things we want to help people to do.

"""
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """A Broad grouping of possible Goals from which users can choose."""
    order = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=128, db_index=True, unique=True)
    name_slug = models.SlugField(max_length=128, db_index=True, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Category"
        verbose_name_plural = "Category"

    @property
    def groups(self):
        return self.interestgroup_set.all()

    @property
    def interests(self):
        ids = self.groups.values_list('interests', flat=True)
        return Interest.objects.filter(id__in=ids).distinct()

    def save(self, *args, **kwargs):
        """Always slugify the name prior to saving the model."""
        self.name_slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('goals:category-detail', args=[self.name_slug])

    def get_update_url(self):
        return reverse('goals:category-update', args=[self.name_slug])

    def get_delete_url(self):
        return reverse('goals:category-delete', args=[self.name_slug])


class Interest(models.Model):
    order = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=128, db_index=True, unique=True)
    name_slug = models.SlugField(max_length=128, db_index=True, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Interest"
        verbose_name_plural = "Interest"

    @property
    def groups(self):
        return self.interestgroup_set.all()

    @property
    def categories(self):
        ids = self.interestgroup_set.values_list('category', flat=True)
        return Category.objects.filter(id__in=ids).distinct()

    def save(self, *args, **kwargs):
        """Always slugify the name prior to saving the model."""
        self.name_slug = slugify(self.name)
        super(Interest, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('goals:interest-detail', args=[self.name_slug])

    def get_update_url(self):
        return reverse('goals:interest-update', args=[self.name_slug])

    def get_delete_url(self):
        return reverse('goals:interest-delete', args=[self.name_slug])

    def remove_from_interestgroups(self):
        """Remove this Interest from the InterestGroups with which it is
        associated. This is called when updateing an Interest, but de-selecting
        InterestGroups.

        """
        for ig in self.groups:
            ig.interests.remove(self)


class InterestGroup(models.Model):
    """This is a model that associates Interests with Categories."""
    category = models.ForeignKey(Category)
    interests = models.ManyToManyField(Interest, blank=True, null=True)
    name = models.CharField(max_length=128)
    public = models.BooleanField(default=True, blank=True)

    def __str__(self):
        return "{0} / {1}".format(self.category, self.name)

    class Meta:
        verbose_name = "Interest Group"
        verbose_name_plural = "Interest Groups"


class Action(models.Model):
    """Actions population the choices of 'I want to...' that users see."""
    FREQUENCY_CHOICES = (
        ('never', 'Never'),
        ('daily', 'Every Day'),
        ('weekly', 'Every Week'),
        ('monthly', 'Every Month'),
        ('yearly', 'Every Year'),
    )
    interests = models.ManyToManyField(Interest)
    order = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=128, db_index=True, unique=True)
    name_slug = models.SlugField(max_length=128, db_index=True, unique=True)
    summary = models.TextField()
    description = models.TextField()
    default_reminder_time = models.TimeField(blank=True, null=True)
    default_reminder_frequency = models.CharField(
        max_length=10,
        blank=True,
        choices=FREQUENCY_CHOICES
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Action'
        verbose_name_plural = 'Action'

    def save(self, *args, **kwargs):
        """Always slugify the name prior to saving the model."""
        self.name_slug = slugify(self.name)
        super(Action, self).save(*args, **kwargs)

    @property
    def groups(self):
        """A Queryset of InterestGroups in which this action is listed."""
        return InterestGroup.objects.filter(interests=self.interests)

    def get_absolute_url(self):
        return reverse('goals:action-detail', args=[self.name_slug])

    def get_update_url(self):
        return reverse('goals:action-update', args=[self.name_slug])

    def get_delete_url(self):
        return reverse('goals:action-delete', args=[self.name_slug])

    def reminder(self, user):
        """Get reminder info for a given user. Returns a tuple of:

            (time, frequency)

        """
        reminder_data = self.get_custom_reminder(user)
        if reminder_data is None:
            reminder_data = (
                self.default_reminder_time,
                self.default_reminder_frequency,
            )
        return reminder_data

    def get_custom_reminder(self, user):
        try:
            cr = CustomReminder.objects.get(user=user, action=self)
            return (cr.time, cr.frequency)
        except CustomReminder.DoesNotExist:
            return None


class CustomReminder(models.Model):
    """A User's custom reminder for an `Action`."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    action = models.ForeignKey(Action)
    time = models.TimeField(blank=True, null=True)
    frequency = models.CharField(
        max_length=10,
        blank=True,
        choices=Action.FREQUENCY_CHOICES
    )

    def __str__(self):
        return 'Custom Reminder for {0}'.format(self.action)

    class Meta:
        ordering = ['action', 'user', 'time']
        unique_together = ('user', 'action')
        verbose_name = 'Custom Reminder'
        verbose_name_plural = 'Custom Reminders'


class SelectedAction(models.Model):
    """An `Action` which a user has selected to attempt to take."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    action = models.ForeignKey(Action)
    date_selected = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return "{0} selected on {1}".format(self.action, self.date_selected)

    class Meta:
        ordering = ['date_selected']
        verbose_name = 'Selected Action'
        verbose_name_plural = 'Selected Actions'

    @property
    def name(self):
        return self.action.name


class ActionTaken(models.Model):
    """When a user _takes_ an `Action`. This is essentially a timestamp that
    records the user's frequency/progress for actions."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    selected_action = models.ForeignKey(SelectedAction)
    date_completed = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return "{0} completed on {1}".format(
            self.selected_action.name,
            self.date_completed
        )

    class Meta:
        ordering = ['date_completed', 'selected_action', 'user']
        verbose_name = 'Action Taken'
        verbose_name_plural = 'Actions Taken'
