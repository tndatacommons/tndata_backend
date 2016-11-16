"""
Public content models for the Goals app. This is our collection of Goals &
related content. They're organized as follows:

    [Category] <-> [Goal] <-> [Action]

Actions are the things we want to help people to do.

"""
import logging
import re

import django.dispatch
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.text import slugify

from django_fsm import FSMField, transition
from django_rq import job
from jsonfield import JSONField
from markdown import markdown
from notifications.models import GCMMessage
from utils import colors
from utils.db import get_max_order

from .organizations import Organization
from .path import (
    _category_icon_path,
    _catetgory_image_path,
    _goal_icon_path,
    _action_icon_path,
)
from .triggers import Trigger
from ..encoder import dump_kwargs
from ..managers import (
    CategoryManager,
    GoalManager,
    WorkflowManager
)
from ..mixins import ModifiedMixin, StateMixin, URLMixin


logger = logging.getLogger(__file__)


class Category(ModifiedMixin, StateMixin, URLMixin, models.Model):
    """A Broad grouping of possible Goals from which users can choose.

    We also have content (goals & actions) that is associated with
    a single organization. We've been referring to this scenario as "packaged
    content", and in this case a Category serves as the Organization's content
    "container".

    """
    DEFAULT_PRIMARY_COLOR = "#2E7D32"
    DEFAULT_SECONDARY_COLOR = "#4CAF50"

    # Grouping. We want to order the listed (featured?) categories by a group
    # (if any) and we want to be able to specify a group's order. SO, the
    # stored DB value indicates order (lower == first) and the name is how
    # things will get listed.
    GROUPING_CHOICES = (
        (-1, "General"),
        (0, "Get ready for college"),
        (1, "Succeed in college"),
        (2, "Help your student succeed"),
        (3, "Featured"),
    )

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
    # -------------------------------------------------------------------------
    # SPECIAL-PURPOSE CATEGORIES:
    #
    # - selected_by_default: These are categories that we want to auto-enroll
    #   new users into. This means they'll have content in the app even if
    #   they don't select anything.
    # - grouping: a way to 'feature' certain categories, but display them in
    #   a named group, together. The grouping value is stored as an integer, so
    #   that we can also sort the groups easily.
    #
    # These are _mutually exclusive_ from packages. They're categories of
    # content, that we make really easy to get the user into the data.
    # -------------------------------------------------------------------------
    selected_by_default = models.BooleanField(
        default=False,
        help_text="Should this category and all of its content be "
                  "auto-selected for new users?"
    )
    grouping = models.IntegerField(
        blank=True,
        null=True,
        default=-1,
        choices=GROUPING_CHOICES,
        help_text="This option defines the section within the app where this "
                  "category will be listed."

    )
    organizations = models.ManyToManyField(
        Organization,
        blank=True,
        related_name="categories",
        help_text="Organizations whose members should have access to this content."
    )
    hidden_from_organizations = models.ManyToManyField(
        Organization,
        blank=True,
        related_name="excluded_categories",
        help_text="Organizations whose members should NOT be able to view "
                  "this category."
    )

    # Contributors are users that should have Editor-equivalent access to the
    # Category and its child content. NOTE: These users *must* also have at
    # least ContentViewer permissions.
    contributors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="category_contributions",
        help_text="The group of users that will contribute to content in "
                  "this category."
    )

    # -------------------------------------------------------------------------
    # PACKAGES.
    # A package is collection of content (just like a category), but it
    # additionally has an extra step required for enrollment; i.e. the user
    # receives a notification, and must agree to a consent form provided by
    # the owner of the package.
    #
    # Until the user does this, they do not gain access to the content within
    # the package. Additionally, differnt package enrollments may contain
    # different goals within the category. Being enrolled in a package does not
    # meant that you have all goals / actions within that category.
    # -------------------------------------------------------------------------
    packaged_content = models.BooleanField(
        default=False,
        help_text="Is this Category for a collection of packaged content?"
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
    # -------------------------------------------------------------------------

    # TIMESTAMPS
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['grouping', 'order', 'title', ]
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        # add_category, change_category, delete_category are created by default.
        permissions = (
            ("view_category", "Can view Categories"),
            ("decline_category", "Can Decline Categories"),
            ("publish_category", "Can Publish Categories"),
        )

    @property
    def featured(self):
        return self.grouping and self.grouping >= 0

    @property
    def grouping_name(self):
        return self.get_grouping_display()

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
    def actions(self):
        """Returns a QuerySet of all Actions nested beneath this category's
        set of Goals. """
        ids = self.goals.values_list('action', flat=True)
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
        if not self.order:
            self.order = get_max_order(self.__class__)
        kwargs = self._check_updated_or_created_by(**kwargs)
        super(Category, self).save(*args, **kwargs)

    @transition(field=state, source="*", target='draft')
    def draft(self):
        """Drafting a Category will also set its child Goals to draft IFF
        they have no other published parent categories; this in turn will cause
        the Actions within that Goal (if drafted) to also be drafted.

        """
        # Fetch all child goals...
        for goal in self.goal_set.filter(state='published'):
            # If they have any other parent categories that are published, just
            # skip over them; other wise unpublish them.
            other_parents = goal.categories.exclude(id=self.id)
            if not other_parents.filter(state='published').exists():
                goal.draft()
                goal.save()  # drafting a goal will draft its child objects

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

    def get_reset_trigger_url(self):
        args = [self.id, self.title_slug]
        return reverse("goals:category-reset-triggers", args=args)

    def get_enroll_url(self):
        return reverse("goals:package-enroll", args=[self.id])

    def get_package_calendar_url(self):
        if self.packaged_content:
            return reverse("goals:package-calendar", args=[self.id])

    def enroll(self, user):
        """Enroll the user in this category and all of the published content
        contained within it."""
        # Enroll the user in this category...
        user.usercategory_set.get_or_create(category=self)

        # Then enroll the user in all of the published Goals
        goals = self.goal_set.filter(state='published')
        for goal in goals:
            ug, _ = user.usergoal_set.get_or_create(user=user, goal=goal)
            ug.primary_category = self
            ug.save()

            # Finally, enroll the user in the Actions
            for action in goal.action_set.published():
                ua, _ = user.useraction_set.get_or_create(action=action)
                ua.primary_category = self
                ua.primary_goal = goal
                ua.save()

    def unenroll(self, user):
        """Removes the user in this category and all of the published content
        contained within it."""
        useractions = user.useraction_set.filter(primary_category__id=self.id)
        useractions.delete()
        user.usergoal_set.filter(primary_category__id=self.id).delete()
        user.usercategory_set.filter(category__id=self.id).delete()

    def duplicate_content(self, prefix="Copy of"):
        """This method will duplicate all of the content stored within this
        Category. That is, we'll create copies of all Goal and Action objects
        that are children for this category.

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
                notes=goal.notes,
                more_info=goal.more_info,
                icon=goal.icon,
                keywords=goal.keywords,
            )
            new_goal.categories.add(new_category)
            new_goal.save()

            for action in goal.action_set.all():
                default_trigger = None
                if action.default_trigger:
                    default_trigger = action.default_trigger
                    default_trigger.pk = None  # HACK to get a new object.
                    default_trigger.name = "{} {}".format(
                        prefix,
                        action.default_trigger.name
                    )
                    default_trigger.save()

                new_action = Action.objects.create(
                    title=action.title,
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
                new_action.goals.add(goal)

        return new_category

    objects = CategoryManager()


@job
def _enroll_program_members(goal):
    """When we publish a Goal, we need to look up the programs in which it
    is listed (e.g. it's a member of Program.auto_enrolled_goals). Then, enroll
    all program members in this goal."""
    User = get_user_model()
    members = goal.program_set.values_list('members', flat=True)
    for user in User.objects.filter(pk__in=members):
        goal.enroll(user)


class Goal(ModifiedMixin, StateMixin, URLMixin, models.Model):

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
        max_length=256,
        db_index=True,
        help_text="A Title for the Goal (50 characters)"
    )
    sequence_order = models.IntegerField(
        default=0,
        db_index=True,
        blank=True,
        help_text="Optional ordering for a sequence of goals"
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
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}".format(self.title)

    class Meta:
        ordering = ['sequence_order', 'title']
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
    def order(self):
        return self.sequence_order

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

        """
        self.title_slug = slugify(self.title)
        self._clean_keywords()
        if self.id:
            parents = self.categories.published().values_list("id", flat=True)
            self.category_ids = list(parents)
        kwargs = self._check_updated_or_created_by(**kwargs)
        super(Goal, self).save(*args, **kwargs)

    @transition(field=state, source="*", target='draft')
    def draft(self):
        """Drafting a Goal will also set its published child Actions to draft
        IFF they have no other published parent goals.

        """
        # Fetch all child actions...
        for action in self.action_set.filter(state='published'):
            # If they have any other parent goals that are published, just
            # skip over them; other wise unpublish them.
            other_parents = action.goals.exclude(id=self.id)
            if not other_parents.filter(state='published').exists():
                action.draft()
                action.save()

    @transition(field=state, source=["draft", "declined"], target='pending-review')
    def review(self):
        pass

    @transition(field=state, source="pending-review", target='declined')
    def decline(self):
        pass

    @transition(field=state, source=["draft", "pending-review"], target='published')
    def publish(self):
        """When a Goal is published, we need to check if it's part of a Program
        whose members should be auto-enrolled in the Goal."""
        _enroll_program_members.delay(self)

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

    def enroll(self, user, primary_category=None):
        """Enroll the user in this goal and all of the published content
        contained within it.

        * user - The user to enroll in the goal.
        * primary_category - If provided, this Category instance will be set
          as the primary category on all UserGoals and UserActions.

        """
        if primary_category is None:
            primary_category = self.get_parent_category_for_user(user)

        # Ensure we also have the category selected.
        if not user.usercategory_set.filter(category=primary_category).exists():
            user.usercategory_set.create(category=primary_category)

        ug, _ = user.usergoal_set.get_or_create(goal=self)
        ug.primary_category = primary_category
        ug.save()

        # Finally, enroll the user in the Actions
        actions = self.action_set.filter(state='published').distinct()
        for action in actions:
            ua, _ = user.useraction_set.get_or_create(action=action)
            ua.primary_category = primary_category
            ua.primary_goal = self
            ua.save()

    objects = GoalManager()


@job
def _remove_queued_messages_for_action(action_id):
    """An Async task that will delete GCMMessages that are associated with
    the given Action.id."""
    try:
        action = Action.objects.get(pk=action_id)

        # We need the content type for this object because we'll use it to
        # query the queued messages.
        action_type = ContentType.objects.get_for_model(action)

        params = {
            'content_type': action_type,
            'object_id': action_id,
            'success': None,  # only messages that haven't been sent.
        }
        GCMMessage.objects.filter(**params).delete()
    except Action.DoesNotExist:
        msg = "Could not remove GCMMessages for Action.id = {}"
        logger.error(msg.format(action_id))


class Action(URLMixin, ModifiedMixin, StateMixin, models.Model):
    """Actions are essentially the content of a Notification. They are things
    that we ask people to do or that reinforce a Goal.

    Actions have an `action_type` which is a just a label for a content author.
    For example, the `REINFORCING` action type will contain contant that
    reinforces some goal while the `SHOWING` action type should contain
    content that models how to do something specific.

    """

    # Action Types are just labels. They denote different "classes" of content
    # and are used by content authors to group similar kinds of messages
    REINFORCING = 'reinforcing'
    ENABLING = 'enabling'
    SHOWING = 'showing'
    STARTER = "starter"
    TINY = "tiny"
    RESOURCE = "resource"
    NOW = "now"
    LATER = "later"
    ASKING = 'asking'  # Asking the user about their current status

    ACTION_TYPE_CHOICES = (
        (SHOWING, 'Showing'),
        (RESOURCE, 'Resource Notification'),
        # (REINFORCING, 'Reinforcing'),
        # (ENABLING, 'Enabling'),
        # (STARTER, 'Starter Step'),
        # (TINY, 'Tiny Version'),
        # (NOW, 'Do it now'),
        # (LATER, 'Do it later'),
        # (ASKING, 'Checkup Notification'),
    )

    # Priorities. Lower number means higher priority, so we can sort.
    LOW = 3
    MEDIUM = 2
    HIGH = 1

    PRIORITY_CHOICES = (
        (LOW, "Default"),
        (MEDIUM, "Medium"),
        (HIGH, "High"),
    )

    # Types for External Resoruces
    EXTERNAL_RESOURCE_TYPES = (
        ('link', 'Link'),
        ('phone', 'Phone Number'),
        ('datetime', 'Date/Time'),
    )

    # URLMixin attributes
    urls_fields = ['pk', 'title_slug']
    urls_app_namespace = "goals"
    urls_model_name = "action"
    urls_icon_field = "icon"
    urls_image_field = "image"
    default_icon = "img/compass-grey.png"

    # Data Fields
    title = models.CharField(
        max_length=256,
        db_index=True,
        help_text="A short (50 character) title for this Action"
    )
    title_slug = models.SlugField(max_length=256, db_index=True)
    goals = models.ManyToManyField(Goal)

    action_type = models.CharField(
        max_length=32,
        default=SHOWING,
        choices=ACTION_TYPE_CHOICES,
        db_index=True,
    )
    sequence_order = models.IntegerField(
        default=0,
        db_index=True,
        help_text="Order/number of action in stepwise sequence."
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
    external_resource_type = models.CharField(
        blank=True,
        max_length=32,
        choices=EXTERNAL_RESOURCE_TYPES,
        help_text=("An internally-used field that makes it easier for client "
                   "apps to determine how to handle the external_resource data.")
    )
    notification_text = models.CharField(
        max_length=256,
        blank=True,
        help_text="Text of the notification (50 characters)"
    )
    icon = models.ImageField(
        upload_to=_action_icon_path,
        null=True,
        blank=True,
        help_text="A square icon for this item in the app, preferrably 512x512."
    )
    state = FSMField(default="draft")
    priority = models.PositiveIntegerField(
        default=LOW,
        choices=PRIORITY_CHOICES,
        help_text="Priority determine how notifications get queued for delivery"
    )
    default_trigger = models.OneToOneField(
        Trigger,
        blank=True,
        null=True,
        help_text="A trigger/reminder for this action",
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
        ordering = ['sequence_order', 'action_type', 'title']
        verbose_name = "Action"
        verbose_name_plural = "Actions"
        # add_action, change_action, delete_action are created by default.
        permissions = (
            ("view_action", "Can view Actions"),
            ("decline_action", "Can Decline Actions"),
            ("publish_action", "Can Publish Actions"),
        )

    def __str__(self):
        return "{}".format(self.title)

    def _set_notification_text(self):
        if not self.notification_text:
            self.notification_text = self.title

    def _serialize_default_trigger(self):
        already_serialized = getattr(self, "_serialized_default_trigger", False)
        if self.default_trigger and not already_serialized:
            from ..serializers.v2 import TriggerSerializer
            srs = TriggerSerializer(self.default_trigger)
            self.serialized_default_trigger = srs.data
            self._serialized_default_trigger = True

    def _set_external_resource_type(self):
        """Set the `external_resource_type` field based on the data detected in
        the `external_resource` field."""
        resource = self.external_resource.strip()
        self.external_resource = resource

        phone_pattern = r'\d\d\d-'
        datetime_pattern = r'\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d'

        # Phone Numbers
        if resource and re.match(phone_pattern, resource):
            self.external_resource_type = 'phone'

        # Links
        elif resource and resource.startswith('http'):
            self.external_resource_type = 'link'

        # Specific Datetimes
        elif resource and re.match(datetime_pattern, resource):
            self.external_resource_type = 'datetime'

    def save(self, *args, **kwargs):
        """After saving an Action, we remove any stale GCM Notifications that
        were associated with the action, IF any of the fields used to generate
        a notification have changed.
        """
        self.title_slug = slugify(self.title)
        kwargs = self._check_updated_or_created_by(**kwargs)
        self._set_notification_text()
        self._serialize_default_trigger()
        self._set_external_resource_type()
        super().save(*args, **kwargs)
        self.remove_queued_messages()  # Note: should be async.

    @property
    def order(self):
        return self.sequence_order

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

        ----

        Spawns an async task and returns a Job.  Returns None if the task
        is not queued (or doesn't need to be)

        """
        job = None
        if not getattr(self, "_removed_queued_messages", False):
            job = _remove_queued_messages_for_action.delay(self.id)
            self._removed_queued_messages = True
        return job

    def get_notification_title(self, goal):
        return goal.title

    def get_notification_text(self):
        return self.notification_text

    @transition(field=state, source="*", target='draft')
    def draft(self):
        """When an Action is reverted to draft (i.e. unpublished) we should
        send a signal so any queued notifications can be deleted."""
        action_unpublished.send(
            sender=self.__class__,
            message=self,
            using='default'
        )

    @transition(field=state, source=["draft", "declined"], target='pending-review')
    def review(self):
        pass

    @transition(field=state, source="pending-review", target='declined')
    def decline(self):
        pass

    @transition(field=state, source=["draft", "pending-review"], target='published')
    def publish(self):
        """When an action is published, we need to auto-enroll all the users
        that have selected the parent goal(s)."""
        pass
        # TODO: For everyone that's selected this action's parent Goals
        # for goal in self.goals.all():
        #   for ug in goal.usergoal_set.all():
        #       ug.add_actions(action_id=self.id)

    objects = WorkflowManager()


# This is a signal that gets fired when an action is unpublished (i.e. reverted
# to a `draft` state. This is implemented as a signal, since we already have a
# signal handler that delete relevant GCM Messages and we want to do the same
# when an Action is unpublished.
_unpublished_args = ['sender', 'instance', 'using']  # same as post-delete
action_unpublished = django.dispatch.Signal(providing_args=_unpublished_args)
