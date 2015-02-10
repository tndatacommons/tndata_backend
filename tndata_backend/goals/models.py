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
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.text import slugify


class Category(models.Model):
    """A Broad grouping of possible Goals from which users can choose."""
    order = models.PositiveIntegerField(
        unique=True,
        help_text="Controls the order in which Categories are displayed."
    )
    name = models.CharField(
        "Title",
        max_length=128, db_index=True, unique=True,
        help_text="A Title for the Category."
    )
    name_slug = models.SlugField(max_length=128, db_index=True, unique=True)
    description = models.TextField(
        help_text="Short description of this Category."
    )
    icon = models.ImageField(
        upload_to="goals/category", null=True, blank=True,
        help_text="Upload an image to be displayed next to the Category."
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes regarding this Category"
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Category"
        verbose_name_plural = "Category"

    @property
    def interests(self):
        """This property returns a QuerySet of the related Interest objects."""
        return self.interest_set.all().distinct()

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


@receiver(post_delete, sender=Category)
def delete_category_icon(sender, instance, using, **kwargs):
    """Once a Category has been deleted, this will remove its icon from the
    filesystem."""
    if instance.icon:
        instance.icon.delete()


class Interest(models.Model):
    """An interest is a broad topic that essentially groups multiple
    behaviors. Interest is more granular than Category.

    """
    categories = models.ManyToManyField(
        Category, blank=True, null=True,
        help_text="Select Categories in which this Interest belongs."
    )
    order = models.PositiveIntegerField(
        unique=True,
        help_text="Controls the order in which Interests are displayed."
    )
    name = models.CharField(
        "Title",
        max_length=128, db_index=True, unique=True,
        help_text="A one-line title for this Interest."
    )
    name_slug = models.SlugField(max_length=128, db_index=True, unique=True)
    description = models.TextField(
        help_text="Short description of this Interest."
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes regarding this Interest."
    )
    source_name = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="The name of the source from which this information was adapted."
    )
    source_link = models.URLField(
        max_length=256,
        blank=True,
        null=True,
        help_text="A link to the source."
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Interest"
        verbose_name_plural = "Interest"

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

    def has_notes(self):
        return any([self.notes, self.source_name, self.source_link])


class InterestGroup(models.Model):
    """This is a model that associates Interests with Categories.
    NOTE: this model is deprecated, but I'm leaving it here for now."
    """
    category = models.ForeignKey(
        Category, help_text="The Category under which this group appears."
    )
    interests = models.ManyToManyField(
        Interest, blank=True, null=True,
        help_text="Select the Interests to group together."
    )
    name = models.CharField(
        "Title",
        max_length=128, db_index=True, unique=True,
        help_text="Give this group a one-line title."
    )
    name_slug = models.SlugField(max_length=128, db_index=True, unique=True)
    public = models.BooleanField(default=True, blank=True)

    def __str__(self):
        return "{0} / {1}".format(self.category, self.name)

    class Meta:
        verbose_name = "Interest Group"
        verbose_name_plural = "Interest Groups"

    def save(self, *args, **kwargs):
        """Always slugify the name prior to saving the model."""
        self.name_slug = slugify(self.name)
        super(InterestGroup, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('goals:group-detail', args=[self.name_slug])

    def get_update_url(self):
        return reverse('goals:group-update', args=[self.name_slug])

    def get_delete_url(self):
        return reverse('goals:group-delete', args=[self.name_slug])


class Action(models.Model):
    """Actions population the choices of 'I want to...' that users see."""
    FREQUENCY_CHOICES = (
        ('never', 'Never'),
        ('daily', 'Every Day'),
        ('weekly', 'Every Week'),
        ('monthly', 'Every Month'),
        ('yearly', 'Every Year'),
    )
    interests = models.ManyToManyField(
        Interest,
        help_text="Select the Interests under which to display this Action."
    )
    order = models.PositiveIntegerField(
        unique=True,
        help_text="Controls the order in which Categories are displayed."
    )
    name = models.CharField(
        "Title",
        max_length=128, db_index=True, unique=True,
        help_text="A one-line title for this Action."
    )
    name_slug = models.SlugField(max_length=128, db_index=True, unique=True)
    summary = models.TextField(
        "Intro Text",
        help_text="A short bit of introductory text that will be displayed "
                  "before the action is selected."
    )
    description = models.TextField(
        "Behavior",
        help_text="The full text of this behavior."
    )
    default_reminder_time = models.TimeField(
        blank=True, null=True,
        help_text="Enter a time in 24-hour format, e.g. 13:30 for 1:30pm"
    )
    default_reminder_frequency = models.CharField(
        max_length=10,
        blank=True,
        choices=FREQUENCY_CHOICES,
        help_text="Choose a default frequency for the reminders."
    )
    icon = models.ImageField(
        upload_to="goals/action", null=True, blank=True,
        help_text="Upload an image to be displayed for this Action."
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes regarding this Category"
    )
    source_name = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="The name of the source from which this information was adapted."
    )
    source_link = models.URLField(
        max_length=256,
        blank=True,
        null=True,
        help_text="A link to the source."
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
        return InterestGroup.objects.filter(interests=self.interests.all())

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

    def has_notes(self):
        return any([self.notes, self.source_name, self.source_link])


@receiver(post_delete, sender=Action)
def delete_action_icon(sender, instance, using, **kwargs):
    """Once an Action has been deleted, this will remove its icon from the
    filesystem."""
    if instance.icon:
        instance.icon.delete()


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
