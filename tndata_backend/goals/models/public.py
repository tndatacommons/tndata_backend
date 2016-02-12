"""
Public content models for the Goals app. This is our collection of Goal &
Behavior content. They're organized as follows:

    [Category] <-> [Goal] <-> [Behavior] <- [Action]

Actions are the things we want to help people to do.

"""
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.text import slugify

from django_fsm import FSMField, transition
from jsonfield import JSONField
from markdown import markdown
from notifications.models import GCMMessage
from utils import colors
from utils.db import get_max_order

from .path import (
    _category_icon_path,
    _catetgory_image_path,
    _goal_icon_path,
    _behavior_icon_path,
)
from .triggers import Trigger
from ..encoder import dump_kwargs
from ..managers import (
    CategoryManager,
    GoalManager,
    WorkflowManager
)
from ..mixins import ModifiedMixin, StateMixin, UniqueTitleMixin, URLMixin


class Category(ModifiedMixin, StateMixin, UniqueTitleMixin, URLMixin, models.Model):
    """A Broad grouping of possible Goals from which users can choose.

    We also have content (goals, behaviors, actions) that is associated with
    a single organization. We've been referring to this scenario as "packaged
    content", and in this case a Category serves as the Organization's content
    "container".

    """
    DEFAULT_PRIMARY_COLOR = "#2E7D32"
    DEFAULT_SECONDARY_COLOR = "#4CAF50"

    # URLMixin attributes
    urls_app_namespace = "goals"
    urls_fields = ['pk', 'title_slug']
    urls_model_name = "category"
    urls_icon_field = "icon"
    urls_image_field = "image"

    # Data Fields. Relevant to all Categories (public and packaged)
    order = models.PositiveIntegerField(
        unique=True,
        help_text="Controls the order in which Categories are displayed."
    )
    title = models.CharField(
        max_length=128,
        db_index=True,
        unique=True,
        help_text="A Title for the Category (50 characters)"
    )
    title_slug = models.SlugField(max_length=128, db_index=True, unique=True)
    description = models.TextField(
        help_text="A short (250 character) description for this Category"
    )
    icon = models.ImageField(
        upload_to=_category_icon_path,
        null=True,
        blank=True,
        help_text="Upload a square icon to be displayed for the Category."
    )
    image = models.ImageField(
        upload_to=_catetgory_image_path,
        null=True,
        blank=True,
        help_text="A Hero image to be displayed at the top of the Category pager"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes regarding this Category"
    )
    color = models.CharField(
        max_length=7,
        default=DEFAULT_PRIMARY_COLOR,
        help_text="Select the color for this Category"
    )
    secondary_color = models.CharField(
        max_length=7,
        blank=True,
        default=DEFAULT_SECONDARY_COLOR,
        help_text="Select a secondary color for this Category. If omitted, a "
                  "complementary color will be generated."
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

    # Fields related to 'Packaged Content'
    packaged_content = models.BooleanField(
        default=False,
        help_text="Is this Category for a collection of packaged content?"
    )
    package_contributors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="packagecontributor_set",
        help_text="The group of users that will contribute to content in "
                  "this category."
    )

    # Packaged content has a consent form (for now anyway). These are only
    # used if a category is marked as a package, and are only available for
    # editing in packages. Both of these should allow markdown.
    consent_summary = models.TextField(blank=True)
    consent_more = models.TextField(blank=True)
    prevent_custom_triggers_default = models.BooleanField(
        default=False,
        help_text="This option determines whether or not custom triggers will "
                  "be allowed by default when enrolling users in the package."
    )
    display_prevent_custom_triggers_option = models.BooleanField(
        default=True,
        help_text="This option determines whether or not package contributors "
                  "will see the option to prevent custom triggers during "
                  "user enrollment."
    )

    # timestamps
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order', 'title']
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        # add_category, change_category, delete_category are created by default.
        permissions = (
            ("view_category", "Can view Categories"),
            ("decline_category", "Can Decline Categories"),
            ("publish_category", "Can Publish Categories"),
        )

    @property
    def is_packaged(self):
        return self.packaged_content

    @property
    def rendered_description(self):
        """Render the description markdown"""
        return markdown(self.description)

    @property
    def rendered_consent_summary(self):
        """Render the consent_summary markdown"""
        return markdown(self.consent_summary)

    @property
    def rendered_consent_more(self):
        """Render the consent_more markdown"""
        return markdown(self.consent_more)

    @property
    def goals(self):
        """This property returns a QuerySet of the related Goal objects."""
        return self.goal_set.all().distinct()

    @property
    def behaviors(self):
        """Returns a QuerySet of all Behaviors nested beneath this category's
        set of goals."""
        ids = self.goals.values_list('behavior', flat=True)
        return Behavior.objects.filter(pk__in=ids)

    @property
    def actions(self):
        """Returns a QuerySet of all Actions nested beneath this category's
        set of Goals & Behaviors. """
        ids = self.behaviors.values_list('action', flat=True)
        return Action.objects.filter(pk__in=ids)

    def _format_color(self, color):
        """Ensure that colors include a # symbol at the beginning."""
        return color if color.startswith("#") else "#{0}".format(color)

    def _generate_secondary_color(self):
        if self.secondary_color:
            return self.secondary_color
        else:
            return colors.lighten(self.color)

    def save(self, *args, **kwargs):
        """Always slugify the name prior to saving the model and set
        created_by or updated_by fields if specified."""
        self.title_slug = slugify(self.title)
        self.color = self._format_color(self.color)
        self.secondary_color = self._generate_secondary_color()
        kwargs = self._check_updated_or_created_by(**kwargs)
        super(Category, self).save(*args, **kwargs)

    @transition(field=state, source="*", target='draft')
    def draft(self):
        pass

    @transition(field=state, source=["draft", "declined"], target='pending-review')
    def review(self):
        pass

    @transition(field=state, source="pending-review", target='declined')
    def decline(self):
        pass

    @transition(field=state, source=["draft", "pending-review"], target='published')
    def publish(self):
        pass

    def get_view_enrollment_url(self):
        """Essentially a Detail view for a Category Package."""
        return reverse("goals:package-detail", args=[self.id])

    def get_enroll_url(self):
        return reverse("goals:package-enroll", args=[self.id])

    def get_package_calendar_url(self):
        if self.packaged_content:
            return reverse("goals:package-calendar", args=[self.id])

    def duplicate_content(self, prefix="Copy of"):
        """This method will duplicate all of the content stored within this
        Category. That is, we'll create copies of all Goal, Behavior, and
        Action objects that are children for this category.

        Every newly created object will be a clone, except for the title, which
        will be prefixed with the given text.

        XXX: This is a potentially slow & inefficient method! Handle with care.

        Returns a copy of the new category.

        """
        new_category = Category.objects.create(
            order=get_max_order(Category),
            title="{} {}".format(prefix, self.title),
            description=self.description,
            icon=self.icon,
            image=self.image,
            notes=self.notes,
            color=self.color,
            secondary_color=self.secondary_color,
            packaged_content=self.packaged_content,
            consent_summary=self.consent_summary,
            consent_more=self.consent_more,
            prevent_custom_triggers_default=self.prevent_custom_triggers_default,
            display_prevent_custom_triggers_option=self.display_prevent_custom_triggers_option,
        )

        for goal in self.goals:
            new_goal, _ = Goal.objects.update_or_create(
                title="{} {}".format(prefix, goal.title),
                description=goal.description,
                subtitle=goal.subtitle,
                outcome=goal.outcome,
                notes=goal.notes,
                more_info=goal.more_info,
                icon=goal.icon,
                keywords=goal.keywords,
            )
            new_goal.categories.add(new_category)
            new_goal.save()

            for behavior in goal.behavior_set.all():
                new_behavior, _ = Behavior.objects.update_or_create(
                    title="{} {}".format(prefix, behavior.title),
                    description=behavior.description,
                    informal_list=behavior.informal_list,
                    source_link=behavior.source_link,
                    source_notes=behavior.source_notes,
                    more_info=behavior.more_info,
                    external_resource=behavior.external_resource,
                    external_resource_name=behavior.external_resource_name,
                    icon=behavior.icon,
                )
                new_behavior.save()
                new_behavior.goals.add(new_goal)

                for action in behavior.action_set.all():
                    default_trigger = None
                    if action.default_trigger:
                        default_trigger = action.default_trigger
                        default_trigger.pk = None
                        default_trigger.name = "{} {}".format(
                            prefix,
                            action.default_trigger.name
                        )
                        default_trigger.save()

                    Action.objects.update_or_create(
                        title="{} {}".format(prefix, action.title),
                        behavior=new_behavior,
                        action_type=action.action_type,
                        sequence_order=action.sequence_order,
                        source_link=action.source_link,
                        source_notes=action.source_notes,
                        notes=action.notes,
                        more_info=action.more_info,
                        description=action.description,
                        external_resource=action.external_resource,
                        external_resource_name=action.external_resource_name,
                        notification_text=action.notification_text,
                        icon=action.icon,
                        default_trigger=default_trigger,
                    )

        return new_category

    objects = CategoryManager()


class Goal(ModifiedMixin, StateMixin, UniqueTitleMixin, URLMixin, models.Model):

    # URLMixin attributes
    urls_app_namespace = "goals"
    urls_fields = ['pk', 'title_slug']
    urls_model_name = "goal"
    urls_icon_field = "icon"

    # Data Fields
    categories = models.ManyToManyField(
        Category,
        blank=True,
        help_text="Select the Categories in which this Goal should appear."
    )
    category_ids = ArrayField(
        models.IntegerField(blank=True),
        default=list,
        blank=True,
        help_text="Pre-rendered list of parent category IDs"
    )

    title_slug = models.SlugField(max_length=256, null=True)
    title = models.CharField(
        max_length=256, db_index=True, unique=True,
        help_text="A Title for the Goal (50 characters)"
    )
    subtitle = models.CharField(
        max_length=256,
        null=True,
        help_text="A one-liner description for this goal."
    )
    description = models.TextField(
        blank=True,
        help_text="A short (250 character) description for this Goal"
    )
    outcome = models.TextField(
        blank=True,
        help_text="Desired outcome of this Goal."
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Misc notes about this item. This is for your use and will "
                  "not be displayed in the app."
    )
    more_info = models.TextField(
        blank=True,
        help_text="Optional tips and tricks or other small, associated ideas. "
                  "Consider using bullets."
    )
    icon = models.ImageField(
        upload_to=_goal_icon_path,
        null=True,
        blank=True,
        help_text="Upload an icon (256x256) for this goal"
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
    keywords = ArrayField(
        models.CharField(max_length=32, blank=True),
        default=list,
        blank=True,
        help_text="Add keywords for this goal. These will be used to generate "
                  "suggestions for the user."
    )
    behaviors_count = models.IntegerField(
        blank=True,
        default=0,
        help_text="The number of (published) child Behaviors in this Goal"
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{0}".format(self.title)

    class Meta:
        ordering = ['title']
        verbose_name = "Goal"
        verbose_name_plural = "Goals"
        # add_goal, change_goal, delete_goal are created by default.
        permissions = (
            ("view_goal", "Can view Goals"),
            ("decline_goal", "Can Decline Goals"),
            ("publish_goal", "Can Publish Goals"),
        )

    def _clean_keywords(self):
        """Split keywords on spaces, lowercase, and strip whitespace."""
        keywords = " ".join(self.keywords).lower()
        self.keywords = [kw.strip() for kw in keywords.split()]

    def get_async_icon_upload_url(self):
        return reverse("goals:file-upload", args=["goal", self.id])

    @property
    def rendered_description(self):
        """Render the description markdown"""
        return markdown(self.description)

    def save(self, *args, **kwargs):
        """This method ensurse we always perform a few tasks prior to saving
        a Goal. These include:

        - Always slugify the title.
        - Always clean keywords (strip & lowercase)
        - Set the updated_by/created_by fields when possible.
        - Set the category_ids if possible
        - Set the behaviors_count field.

        """
        self.title_slug = slugify(self.title)
        self._clean_keywords()
        if self.id:
            parents = self.categories.published().values_list("id", flat=True)
            self.category_ids = list(parents)
            self.behaviors_count = self.behavior_set.published().count()
        kwargs = self._check_updated_or_created_by(**kwargs)
        super(Goal, self).save(*args, **kwargs)

    @transition(field=state, source="*", target='draft')
    def draft(self):
        pass

    @transition(field=state, source=["draft", "declined"], target='pending-review')
    def review(self):
        pass

    @transition(field=state, source="pending-review", target='declined')
    def decline(self):
        pass

    @transition(field=state, source=["draft", "pending-review"], target='published')
    def publish(self):
        pass

    def get_parent_category_for_user(self, user):
        """Return one of this object's parent categories, prefering one that
        the given user has selected.

        * user - A User instance. We return a Category that the user has
          selected if possible.

        """
        user_cats = user.usercategory_set.values_list('category', flat=True)
        cat = self.categories.filter(id__in=user_cats).first()
        if cat is None:
            cat = self.categories.first()
        return cat

    objects = GoalManager()


class Behavior(URLMixin, UniqueTitleMixin, ModifiedMixin, StateMixin, models.Model):
    """A Behavior. Behaviors have many actions associated with them and contain
    several bits of information for a user."""

    # URLMixin attributes
    urls_app_namespace = "goals"
    urls_model_name = "behavior"
    urls_fields = ["pk", "title_slug"]
    urls_icon_field = "icon"
    urls_image_field = "image"

    # Data Fields
    title = models.CharField(
        max_length=256,
        db_index=True,
        unique=True,
        help_text="A unique title for this Behavior (50 characters)"
    )
    title_slug = models.SlugField(max_length=256, db_index=True, unique=True)
    sequence_order = models.IntegerField(
        default=0,
        db_index=True,
        blank=True,
        help_text="Optional ordering for a sequence of behaviors"
    )
    goals = models.ManyToManyField(
        Goal,
        blank=True,
        help_text="Select the Goal(s) that this Behavior achieves."
    )
    goal_ids = ArrayField(
        models.IntegerField(blank=True),
        default=list,
        blank=True,
        help_text="Pre-rendered list of parent goal IDs"
    )
    description = models.TextField(
        blank=True,
        help_text="A brief (250 characters) description about this item."
    )
    informal_list = models.TextField(
        blank=True,
        help_text="Use this section to create a list of specific actions for "
                  "this behavior. This list will be reproduced as a mnemonic "
                  "on the Action entry page"
    )
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
    more_info = models.TextField(
        blank=True,
        help_text="Optional tips and tricks or other small, associated ideas. "
                  "Consider using bullets."
    )
    external_resource = models.CharField(
        blank=True,
        max_length=256,
        help_text=("An external resource is something that will help a user "
                   "accomplish a task. It could be a phone number, link to a "
                   "website, link to another app, or GPS coordinates. ")
    )
    external_resource_name = models.CharField(
        blank=True,
        max_length=256,
        help_text=("A human-friendly name for your external resource. This is "
                   "especially helpful for web links.")
    )
    icon = models.ImageField(
        upload_to=_behavior_icon_path,
        null=True,
        blank=True,
        help_text="A square icon for this item in the app, preferrably 512x512."
    )
    state = FSMField(default="draft")
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
    actions_count = models.IntegerField(
        blank=True,
        default=0,
        help_text="The number of (published) child actions in this Behavior"
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sequence_order', 'title']
        verbose_name = "Behavior"
        verbose_name_plural = "Behaviors"
        # add_behavior, change_behavior, delete_behavior are created by default.
        permissions = (
            ("view_behavior", "Can view Permissions"),
            ("decline_behavior", "Can Decline Permissions"),
            ("publish_behavior", "Can Publish Permissions"),
        )

    def __str__(self):
        return "{0}".format(self.title)

    def save(self, *args, **kwargs):
        """Always slugify the name prior to saving the model."""
        self.title_slug = slugify(self.title)
        kwargs = self._check_updated_or_created_by(**kwargs)
        if self.id:
            self.goal_ids = list(self.goals.values_list('id', flat=True))
            self.actions_count = self.action_set.published().count()
        super().save(*args, **kwargs)

    @property
    def rendered_description(self):
        """Render the description markdown"""
        return markdown(self.description)

    @property
    def rendered_more_info(self):
        """Render the more_info markdown"""
        return markdown(self.more_info)

    @transition(field=state, source="*", target='draft')
    def draft(self):
        pass

    @transition(field=state, source=["draft", "declined"], target='pending-review')
    def review(self):
        pass

    @transition(field=state, source="pending-review", target='declined')
    def decline(self):
        pass

    @transition(field=state, source=["draft", "pending-review"], target='published')
    def publish(self):
        pass

    def get_async_icon_upload_url(self):
        return reverse("goals:file-upload", args=["behavior", self.id])

    @property
    def categories(self):
        """Return a QuerySet of Categories for this object's selected Goals"""
        cats = self.goals.values_list('categories', flat=True)
        return Category.objects.filter(pk__in=cats)

    def get_user_mapping(self, user):
        """Return the first UserBehavior object that matches this Behavior and
        the given user. There _should_ only be one of these. Returns None if
        the object is not found.

        Note: This method can be used by other apps that may have a generic
        relationships (e.g. notifications).

        """
        return self.userbehavior_set.filter(user=user, behavior=self).first()

    objects = WorkflowManager()


class Action(URLMixin, ModifiedMixin, StateMixin, models.Model):
    """Actions are things that people do, and are typically the bit of
    information to which a user will set a reminder (e.g. a Trigger).

    Actions can be of different types, i.e.:

    * Starter Step
    * Tiny Version
    * Resource
    * Right now
    * Custom

    """
    STARTER = "starter"
    TINY = "tiny"
    RESOURCE = "resource"
    NOW = "now"
    LATER = "later"
    CUSTOM = "custom"

    ACTION_TYPE_CHOICES = (
        (STARTER, 'Starter Step'),
        (TINY, 'Tiny Version'),
        (RESOURCE, 'Resource'),
        (NOW, 'Do it now'),
        (LATER, 'Do it later'),
        (CUSTOM, 'Custom'),
    )

    # URLMixin attributes
    urls_fields = ['pk', 'title_slug']
    urls_app_namespace = "goals"
    urls_model_name = "action"
    urls_icon_field = "icon"
    urls_image_field = "image"
    default_icon = "img/compass-grey.png"

    # String formatting patters for notifications
    _notification_title = "To {}:"  # Fill with the primary goal.
    _notification_text = "Remember to {}"  # Fill with the notification_text

    # Data Fields
    title = models.CharField(
        max_length=256,
        db_index=True,
        help_text="A short (50 character) title for this Action"
    )
    title_slug = models.SlugField(max_length=256, db_index=True)

    behavior = models.ForeignKey(Behavior, verbose_name="behavior")
    action_type = models.CharField(
        max_length=32,
        default=CUSTOM,
        choices=ACTION_TYPE_CHOICES,
        db_index=True,
    )
    sequence_order = models.IntegerField(
        default=0,
        db_index=True,
        help_text="Order/number of action in stepwise sequence of behaviors"
    )

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
    more_info = models.TextField(
        blank=True,
        help_text="Optional tips and tricks or other small, associated ideas. "
                  "Consider using bullets."
    )
    description = models.TextField(
        blank=True,
        help_text="A brief (250 characters) description about this item."
    )
    external_resource = models.CharField(
        blank=True,
        max_length=256,
        help_text=("An external resource is something that will help a user "
                   "accomplish a task. It could be a phone number, link to a "
                   "website, link to another app, or GPS coordinates. ")
    )
    external_resource_name = models.CharField(
        blank=True,
        max_length=256,
        help_text=("A human-friendly name for your external resource. This is "
                   "especially helpful for web links.")
    )
    notification_text = models.CharField(
        max_length=256,
        blank=True,
        help_text="Text of the notification (50 characters)"
    )
    icon = models.ImageField(
        upload_to=_behavior_icon_path,
        null=True,
        blank=True,
        help_text="A square icon for this item in the app, preferrably 512x512."
    )
    state = FSMField(default="draft")
    default_trigger = models.OneToOneField(
        Trigger,
        blank=True,
        null=True,
        help_text="A trigger/reminder for this behavior",
        related_name="action_default"
    )
    # pre-serialize the default trigger for the api, so we can avoid some joins
    serialized_default_trigger = JSONField(
        blank=True,
        default=dict,
        dump_kwargs=dump_kwargs
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
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sequence_order', 'title']
        verbose_name = "Action"
        verbose_name_plural = "Actions"
        # add_action, change_action, delete_action are created by default.
        permissions = (
            ("view_action", "Can view Actions"),
            ("decline_action", "Can Decline Actions"),
            ("publish_action", "Can Publish Actions"),
        )

    def __str__(self):
        return "{0}".format(self.title)

    def _set_notification_text(self):
        if not self.notification_text:
            self.notification_text = self.title

    @classmethod
    def get_create_starter_action_url(cls):
        return "{0}?actiontype={1}".format(
            reverse("goals:action-create"), cls.STARTER)

    @classmethod
    def get_create_tiny_action_url(cls):
        return "{0}?actiontype={1}".format(
            reverse("goals:action-create"), cls.TINY)

    @classmethod
    def get_create_resource_action_url(cls):
        return "{0}?actiontype={1}".format(
            reverse("goals:action-create"), cls.RESOURCE)

    @classmethod
    def get_create_now_action_url(cls):
        return "{0}?actiontype={1}".format(
            reverse("goals:action-create"), cls.NOW)

    @classmethod
    def get_create_later_action_url(cls):
        return "{0}?actiontype={1}".format(
            reverse("goals:action-create"), cls.LATER)

    @classmethod
    def get_create_custom_action_url(cls):
        return "{0}?actiontype={1}".format(
            reverse("goals:action-create"), cls.CUSTOM)

    def _serialize_default_trigger(self):
        if self.default_trigger:
            from ..serializers.v2 import TriggerSerializer
            srs = TriggerSerializer(self.default_trigger)
            self.serialized_default_trigger = srs.data

    def save(self, *args, **kwargs):
        """After saving an Action, we remove any stale GCM Notifications that
        were associated with the action, IF any of the fields used to generate
        a notification have changed.
        """
        self.title_slug = slugify(self.title)
        kwargs = self._check_updated_or_created_by(**kwargs)
        self._set_notification_text()
        self._serialize_default_trigger()
        super().save(*args, **kwargs)
        self.remove_queued_messages()

    @property
    def rendered_description(self):
        """Render the description markdown"""
        return markdown(self.description)

    @property
    def rendered_more_info(self):
        """Render the more_info markdown"""
        return markdown(self.more_info)

    def get_disable_trigger_url(self):
        args = [self.id, self.title_slug]
        return reverse("goals:action-disable-trigger", args=args)

    def disable_default_trigger(self):
        """Remove the default trigger from this action."""
        trigger_id = self.default_trigger.pk
        self.default_trigger = None
        self.save()

        # Delete the now-orphaned trigger
        Trigger.objects.filter(pk=trigger_id).delete()

    def get_async_icon_upload_url(self):
        return reverse("goals:file-upload", args=["action", self.id])

    def get_user_mapping(self, user):
        """Return the first UserAction object that matches this Action and the
        given user. There _should_ only be one of these. Returns None if the
        object is not found.

        Note: This method can be used by other apps that may have a generic
        relationships (e.g. notifications).

        """
        return self.useraction_set.filter(user=user, action=self).first()

    def remove_queued_messages(self):
        """Remove all GCMMessage objects that have a GenericForeignKey to this
        action instance.

        Once removed, the scheduled task will re-created any messages that need
        to be sent in the future.

        Historical note: I tried to check if fields had changed before doing
        this, but it was _hard_ with the related default_trigger field (because
        local values would be different types than what I read from the DB).
        I used something like: http://stackoverflow.com/a/15280630/182778 to
        build:

            _changed(['notification_text', 'default_trigger__time', ... ])

        """
        if not getattr(self, "_removed_queued_messages", False):
            # We need the content type for this object because we'll use it to
            # query the queued messages.
            action_type = ContentType.objects.get_for_model(self)

            params = {
                'content_type': action_type,
                'object_id': self.id,
                'success': None,  # only messages that haven't been sent.
            }
            GCMMessage.objects.filter(**params).delete()
            self._removed_queued_messages = True

    def get_notification_title(self, goal):
        # Let's try to un-capitalize the first character, but only if:
        # 1. it's not already lowercase, and
        # 2. the 2nd character isn't lowercase.
        title = goal.title
        if len(title) > 2 and not title[0:2].isupper():
            title = "{}{}".format(title[0].lower(), title[1:])
            return self._notification_title.format(title)
        return self._notification_title.format(title)

    def get_notification_text(self):
        text = self.notification_text
        if len(text) > 2 and not text[0:2].isupper():
            text = "{}{}".format(text[0].lower(), text[1:])
            return self._notification_text.format(text)
        return self._notification_text.format(text)

    @transition(field=state, source="*", target='draft')
    def draft(self):
        pass

    @transition(field=state, source=["draft", "declined"], target='pending-review')
    def review(self):
        pass

    @transition(field=state, source="pending-review", target='declined')
    def decline(self):
        pass

    @transition(field=state, source=["draft", "pending-review"], target='published')
    def publish(self):
        pass

    objects = WorkflowManager()
