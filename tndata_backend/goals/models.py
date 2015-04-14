"""Models for the Goals app.

This is our collection of Goals & Behaviors. They're organized as follows:

    [Category] <-> [Goal] <-> [Behavior] <- [Action]

Actions are the things we want to help people to do.

"""
import os

from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.text import slugify
from django_fsm import FSMField

from .mixins import URLMixin, WorkflowMixin

# TODO: Permissions for CRUD operations on the content models?
# TODO: Update Views to give Eidtors a "dashboard"


class Category(URLMixin, WorkflowMixin, models.Model):
    """A Broad grouping of possible Goals from which users can choose."""

    # URLMixin attributes
    urls_app_namespace = "goals"
    urls_model_name = "category"
    urls_icon_field = "icon"

    # Data Fields
    order = models.PositiveIntegerField(
        unique=True,
        help_text="Controls the order in which Categories are displayed."
    )
    title = models.CharField(
        max_length=128,
        db_index=True,
        unique=True,
        help_text="A Title for the Category."
    )
    title_slug = models.SlugField(max_length=128, db_index=True, unique=True)
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
    state = FSMField(default="draft")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="categories_updated",
        null=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="categories_created",
        null=True
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order', 'title']
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    @property
    def goals(self):
        """This property returns a QuerySet of the related Goal objects."""
        return self.goal_set.all().distinct()

    def save(self, *args, **kwargs):
        """Always slugify the name prior to saving the model."""
        self.title_slug = slugify(self.title)
        super(Category, self).save(*args, **kwargs)


class Goal(URLMixin, WorkflowMixin, models.Model):

    # URLMixin attributes
    urls_app_namespace = "goals"
    urls_model_name = "goal"
    urls_icon_field = "icon"

    # Data Fields
    categories = models.ManyToManyField(
        Category, null=True, blank=True,
        help_text="Select the Categories in which this Goal should appear."
    )
    title_slug = models.SlugField(max_length=256, null=True)
    title = models.CharField(
        max_length=256, db_index=True, unique=True,
        help_text="A public Title for this goal."
    )
    subtitle = models.CharField(
        max_length=256,
        null=True,
        help_text="A one-liner description for this goal."
    )
    description = models.TextField(
        blank=True,
        help_text="Short description of this Category."
    )
    outcome = models.TextField(
        blank=True,
        help_text="Desired outcome of this Goal."
    )
    icon = models.ImageField(
        upload_to="goals/goal", null=True, blank=True,
        help_text="Upload an image to be displayed next to the Goal."
    )
    state = FSMField(default="draft")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="goals_updated",
        null=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="goals_created",
        null=True
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{0}".format(self.title)

    class Meta:
        verbose_name = "Goal"
        verbose_name_plural = "Goals"

    def save(self, *args, **kwargs):
        """Always slugify the title prior to saving the model."""
        self.title_slug = slugify(self.title)
        super(Goal, self).save(*args, **kwargs)


class Trigger(URLMixin, models.Model):
    """Information for a Trigger/Notificatin/Reminder. This may include date,
    time, location and a frequency with which triggers repeat.

    """

    # URLMixin attributes
    urls_app_namespace = "goals"
    urls_model_name = "trigger"
    urls_slug_field = "name_slug"

    # Data Fields
    TRIGGER_TYPES = (
        ('time', 'Time'),
        ('place', 'Place'),
    )
    FREQUENCY_CHOICES = (
        ('one-time', 'One Time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    )
    name = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
        help_text="Give this trigger a helpful name. It must be unique, and "
                  "will be used in drop-down lists and other places where you"
                  "can select it later."
    )
    name_slug = models.SlugField(max_length=128, db_index=True, unique=True)
    trigger_type = models.CharField(
        blank=True,
        max_length=10,
        choices=TRIGGER_TYPES,
        help_text='The type of Trigger used, e.g. Time, Place, etc'
    )
    frequency = models.CharField(
        blank=True,
        max_length=10,
        choices=FREQUENCY_CHOICES,
        help_text="How frequently a trigger is fired"
    )
    time = models.TimeField(
        blank=True,
        null=True,
        help_text="Time the trigger/notification will fire, in 24-hour format."
    )
    date = models.DateField(
        blank=True,
        null=True,
        help_text="The date of the trigger/notification. If the trigger is "
                  "recurring, notifications will start on this date."
    )
    location = models.CharField(
        max_length=256,
        blank=True,
        help_text="Only used when Trigger type is location. "
                  "Can be 'home', 'work', or a (lat, long) pair."
    )
    text = models.CharField(
        max_length=140,
        blank=True,
        help_text="The Trigger text shown to the user."
    )
    instruction = models.TextField(
        blank=True,
        help_text="Instructions sent to the user."
    )

    def __str__(self):
        return "{0}".format(self.name)

    class Meta:
        verbose_name = "Trigger"
        verbose_name_plural = "Triggers"

    def save(self, *args, **kwargs):
        """Always slugify the name prior to saving the model."""
        self.name_slug = slugify(self.name)
        super(Trigger, self).save(*args, **kwargs)


def _behavior_icon_path(instance, filename):
    """Return the path for uploaded icons for `Behavior` and `Action` objects."""
    p = "goals/{0}/icons".format(type(instance).__name__.lower())
    return os.path.join(p, filename)


def _behavior_img_path(instance, filename):
    """Return the path for uploaded images for `Behavior` and `Action` objects."""
    p = "goals/{0}/images".format(type(instance).__name__.lower())
    return os.path.join(p, filename)


class BaseBehavior(models.Model):
    """This abstract base class contains fields that are common to both
    `Behavior` and `Action` models.

    """
    title = models.CharField(
        max_length=256,
        db_index=True,
        unique=True,
        help_text="A unique title for this item. This will be displayed in the app."
    )
    title_slug = models.SlugField(max_length=256, db_index=True, unique=True)
    source_link = models.URLField(
        max_length=256,
        blank=True,
        null=True,
        help_text="A link to the source."
    )
    source_notes = models.TextField(
        blank=True,
        help_text="Narrative notes about the source of this item."
    )
    notes = models.TextField(
        blank=True,
        help_text="Misc notes about this item. This is for your use and will "
                  "not be displayed in the app."
    )
    narrative_block = models.TextField(
        blank=True,
        help_text="Persuasive narrative description: Tell the user why this is imporrtant."
    )
    description = models.TextField(blank=True, help_text="A brief description about this item.")
    case = models.TextField(
        blank=True,
        help_text="Brief description of why this is useful."
    )
    outcome = models.TextField(
        blank=True,
        help_text="Brief description of what the user can expect to get by "
                  "adopting the behavior"
    )
    external_resource = models.CharField(
        blank=True,
        max_length=256,
        help_text="A link or reference to an outside resource necessary for adoption"
    )
    default_trigger = models.ForeignKey(
        Trigger,
        blank=True,
        null=True,
        help_text="A trigger/reminder for this behavior"
    )
    notification_text = models.CharField(
        max_length=256,
        blank=True,
        help_text="Text message delivered through notification channel"
    )
    icon = models.ImageField(
        upload_to=_behavior_icon_path,
        null=True,
        blank=True,
        help_text="A square icon for this item in the app, preferrably 512x512."
    )
    image = models.ImageField(
        upload_to=_behavior_img_path,
        null=True,
        blank=True,
        help_text="An image to be displayed for this item, preferrably 1024x1024."
    )
    state = FSMField(default="draft")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return "{0}".format(self.title)

    def save(self, *args, **kwargs):
        """Always slugify the name prior to saving the model."""
        self.title_slug = slugify(self.title)
        super(BaseBehavior, self).save(*args, **kwargs)


class Behavior(URLMixin, WorkflowMixin, BaseBehavior):
    """A Behavior. Behaviors have many actions associated with them and contain
    several bits of information for a user."""

    # URLMixin attributes
    urls_app_namespace = "goals"
    urls_model_name = "behavior"
    urls_icon_field = "icon"
    urls_image_field = "image"

    # Data Fields
    categories = models.ManyToManyField(
        Category, null=True, blank=True,
        help_text="Select the Categories in which this should appear."
    )
    goals = models.ManyToManyField(
        Goal, null=True, blank=True,
        help_text="Select the Goal(s) that this Behavior achieves."
    )
    informal_list = models.TextField(
        blank=True,
        help_text="A working list of actions for the behavior. Mnemonic only."
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="behaviors_updated",
        null=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="behaviors_created",
        null=True
    )

    class Meta(BaseBehavior.Meta):
        verbose_name = "Behavior"
        verbose_name_plural = "Behaviors"


class Action(URLMixin, WorkflowMixin, BaseBehavior):

    # URLMixin attributes
    urls_app_namespace = "goals"
    urls_model_name = "action"
    urls_icon_field = "icon"
    urls_image_field = "image"

    # Data Fields
    behavior = models.ForeignKey(Behavior, verbose_name="behavior")
    sequence_order = models.IntegerField(
        default=0, db_index=True,
        help_text="Order/number of action in stepwise sequence of behaviors"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="actions_updated",
        null=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="actions_created",
        null=True
    )

    class Meta(BaseBehavior.Meta):
        verbose_name = "Action"
        verbose_name_plural = "Actions"


@receiver(post_delete, sender=Action)
@receiver(post_delete, sender=Behavior)
@receiver(post_delete, sender=Goal)
@receiver(post_delete, sender=Category)
def delete_model_icon(sender, instance, using, **kwargs):
    """Once a model instance has been deleted, this will remove its `icon` from
    the filesystem."""
    if hasattr(instance, 'icon') and instance.icon:
        instance.icon.delete()


@receiver(post_delete, sender=Action)
@receiver(post_delete, sender=Behavior)
def delete_model_image(sender, instance, using, **kwargs):
    """Once a model instance has been deleted, this will remove its `image`
    from the filesystem."""
    if hasattr(instance, 'image') and instance.image:
        instance.image.delete()


# -----------------------------------------------------------------------------
#
# Models that track a user's progress toward Goals, Behaviors, Actions.
#
# -----------------------------------------------------------------------------
class UserGoal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    goal = models.ForeignKey(Goal)
    completed = models.BooleanField(default=False)
    completed_on = models.DateTimeField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{0}".format(self.goal.title)

    class Meta:
        ordering = ['user', 'goal']
        unique_together = ("user", "goal")
        verbose_name = "User Goal"
        verbose_name_plural = "User Goals"

    def get_user_categories(self):
        """Returns a QuerySet of Categories related to this Goal, but restricts
        those categories to those which the user has selected."""
        cids = self.user.usercategory_set.values_list('category__id', flat=True)
        return self.goal.categories.filter(id__in=cids)


class UserBehavior(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    behavior = models.ForeignKey(Behavior)
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


class UserAction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    action = models.ForeignKey(Action)
    completed = models.BooleanField(default=False)
    completed_on = models.DateTimeField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{0}".format(self.action.title)

    class Meta:
        ordering = ['user', 'action']
        unique_together = ("user", "action")
        verbose_name = "User Action"
        verbose_name_plural = "User Actions"


class UserCategory(models.Model):
    """A Mapping between users and specific categories."""
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

    def get_user_goals(self):
        """Returns a QuerySet of Goals related to this Category, but restricts
        those goals to those which the user has selected."""
        gids = self.user.usergoal_set.values_list('goal__id', flat=True)
        return self.category.goals.filter(id__in=gids)
