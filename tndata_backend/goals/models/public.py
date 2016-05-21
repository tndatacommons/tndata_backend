"""
Public content models for the Goals app. This is our collection of Goal &
Behavior content. They're organized as follows:

    [Category] <-> [Goal] <-> [Behavior] <- [Action]

Actions are the things we want to help people to do.

"""
from collections import defaultdict

import django.dispatch
from django.conf import settings
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

from .path import (
    _category_icon_path,
    _catetgory_image_path,
    _goal_icon_path,
    _behavior_icon_path,
)
from .triggers import Trigger
from ..encoder import dump_kwargs
from ..managers import (
    BehaviorManager,
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
    # -------------------------------------------------------------------------
    # SPECIAL-PURPOSE CATEGORIES:
    #
    # - selected_by_default: These are categories that we want to auto-enroll
    #   new users into. This means they'll have content in the app even if
    #   they don't select anything.
    # - featured: Thes are categories that should get listed prominently in the
    #   app, typically for a provider we want to promote.
    #
    # These are _mutually exclusive_ from packages. They're categories of
    # content, that we make really easy to get the user into the data.
    # -------------------------------------------------------------------------
    selected_by_default = models.BooleanField(
        default=False,
        help_text="Should this category and all of its content be "
                  "auto-selected for new users?"
    )
    featured = models.BooleanField(
        default=False,
        help_text="Featured categories are typically collection of content "
                  "provided by an agency/partner that we want to promote "
                  "publicy within the app."
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
    # meant that you have all goals / behaviors / actions within that category.
    # -------------------------------------------------------------------------
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
    # -------------------------------------------------------------------------

    # TIMESTAMPS
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order', 'title', 'featured', ]
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
        if not self.order:
            self.order = get_max_order(self.__class__)
        kwargs = self._check_updated_or_created_by(**kwargs)
        super(Category, self).save(*args, **kwargs)

    @transition(field=state, source="*", target='draft')
    def draft(self):
        """Drafting a Category will also set its child Goals to draft IFF
        they have no other published parent categories; this in turn will cause
        the Behaviors & Actions within that Goal (if drafted) to also be drafted.

        """
        # Fetch all child goals...
        for goal in self.goal_set.filter(state='published'):
            # If they have any other parent categories that are published, just
            # skip over them; other wise unpublish them.
            other_parents = goal.categories.exclude(id=self.id)
            if not other_parents.filter(state='published').exists():
                goal.draft()
                goal.save()  # drafting a goal will draft its child behaviors

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

        # Then enroll the user in the published Behaviors
        behaviors = Behavior.objects.published().filter(goals=goals).distinct()
        for behavior in behaviors:
            user.userbehavior_set.get_or_create(behavior=behavior)

        # Finally, enroll the user in the Behavior's Actions
        actions = Action.objects.published().filter(behavior__in=behaviors)
        for action in actions.distinct():
            ua, _ = user.useraction_set.get_or_create(action=action)
            ua.primary_category = self
            ua.primary_goal = ua.get_primary_goal()
            ua.save()

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
        """Drafting a Goal will also set its published child Behaviors to draft
        IFF they have no other published parent goals; this in turn will cause
        the Actions within that behavior (if drafted) to also be drafted.

        """
        # Fetch all child behaviors...
        for behavior in self.behavior_set.filter(state='published'):
            # If they have any other parent goals that are published, just
            # skip over them; other wise unpublish them.
            other_parents = behavior.goals.exclude(id=self.id)
            if not other_parents.filter(state='published').exists():
                behavior.draft()
                behavior.save()  # drafting a behavior will draft its Actions.

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

        # Then enroll the user in the published Behaviors
        behaviors = Behavior.objects.published().filter(goals=self).distinct()
        for behavior in behaviors:
            user.userbehavior_set.get_or_create(behavior=behavior)

        # Finally, enroll the user in the Behavior's Actions
        actions = Action.objects.published().filter(behavior__in=behaviors)
        for action in actions.distinct():
            ua, _ = user.useraction_set.get_or_create(action=action)
            ua.primary_category = primary_category
            ua.primary_goal = self
            ua.save()

    objects = GoalManager()


@job
def _enroll_users_in_published_behavior(behavior):
    """When we publish a behavior, we need to enroll everyone that has selected
    the behavior's parents' (goal) and in all the published child actions."""
    for goal in behavior.goals.published():
        # For everyone that's selected the parent Goals:
        for ug in goal.usergoal_set.all():
            ug.add_behaviors(behaviors=[behavior])


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
    # -----------
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

    # Reporting roll-up fields
    # ------------------------
    actions_count = models.IntegerField(
        blank=True,
        default=0,
        help_text="The number of (published) child actions in this Behavior"
    )
    action_buckets_prep = models.IntegerField(
        blank=True,
        default=0,
        help_text="The number of PREP actions in this behavior."
    )
    action_buckets_core = models.IntegerField(
        blank=True,
        default=0,
        help_text="The number of CORE actions in this behavior."
    )
    action_buckets_helper = models.IntegerField(
        blank=True,
        default=0,
        help_text="The number of HELPER actions in this behavior."
    )
    action_buckets_checkup = models.IntegerField(
        blank=True,
        default=0,
        help_text="The number of CHECKUP actions in this behavior."
    )
    # Record-keeping on who/when this was last changed this behavior
    # --------------------------------------------------------------
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
        return "{}".format(self.title)

    def _set_goal_ids(self):
        """Save the parent Goal IDs in the `goal_ids` array field; this should
        get called every time the Behavior is saved."""
        if self.id:
            self.goal_ids = list(self.goals.values_list('id', flat=True))

    def _count_actions(self):
        """Count this behavior's child actions, and store a breakdown of
        how many exist in each bucket (if they're dynamic)"""
        if self.id:
            # Count all of our published actions.
            self.actions_count = self.action_set.published().count()

            # Count the number of Actions in each bucket
            qs = self.action_set.all()
            self.action_buckets_prep = qs.filter(bucket=Action.PREP).count()
            self.action_buckets_core = qs.filter(bucket=Action.CORE).count()
            self.action_buckets_helper = qs.filter(bucket=Action.HELPER).count()
            self.action_buckets_checkup = qs.filter(bucket=Action.CHECKUP).count()

    def save(self, *args, **kwargs):
        """Always slugify the name prior to saving the model."""
        self.title_slug = slugify(self.title)
        kwargs = self._check_updated_or_created_by(**kwargs)
        self._set_goal_ids()
        self._count_actions()
        super().save(*args, **kwargs)

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

    @transition(field=state, source="*", target='draft')
    def draft(self):
        """Setting a behavior to draft will also draft it's child Actions."""
        self.action_set.filter(state='published').update(state='draft')

    @transition(field=state, source=["draft", "declined"], target='pending-review')
    def review(self):
        pass

    @transition(field=state, source="pending-review", target='declined')
    def decline(self):
        pass

    @transition(field=state, source=["draft", "pending-review"], target='published')
    def publish(self):
        """
        When a Behavior is published, we need to auto-enroll all of the users
        that have selected the parent goal, AND look for all of the child
        Actions that are published, and auto-enroll the user in those as well.

        NOTE: this is impolemented as an async job since it'll be slow.

        """
        _enroll_users_in_published_behavior.delay(self)

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

    def contains_dynamic(self):
        """Returns True or False; This method tells us if this Behavior
        contains any dynamic notifications; i.e. Actions that have a bucket,
        and whose default trigger contains a time_of_day and frequency value.

        NOTE: This behavior may also contain some NON-Dynamic actions, as well.

        """
        actions = self.action_set.filter(
            default_trigger__time_of_day__isnull=False,
            default_trigger__frequency__isnull=False
        )
        return actions.distinct().exists()

    def action_buckets(self):
        """Return a dictionary of this Behavior's published Actions organized
        by bucket. The dict is of the form:

            {bucket: [Action, ...]}

        """
        buckets = defaultdict(list)
        for action in self.action_set.published():
            buckets[action.bucket].append(action)
        return dict(buckets)

    objects = BehaviorManager()


def _action_type_url_function(action_type):
    """Return a function that reverses the Create Action url, but includes the
    given action type. The returned function expects one argument (the class)
    and can be used as a @classmethod."""
    def _reverse_url(cls):
        url = reverse('goals:action-create')
        return "{}?actiontype={}".format(url, action_type)
    return _reverse_url


class Action(URLMixin, ModifiedMixin, StateMixin, models.Model):
    """Actions are essentially the content of a Notification. They are things
    that we ask people to do or that reinforce a Behavior.

    Actions have an `action_type` which is a just a label for a content author.
    For example, the `REINFORCING` action type will contain contant that
    reinforces some behavior while the `SHOWING` action type should contain
    content that models how to do something specific.

    Actions are also placed within a "bucket", and this defines how an autotmatic
    nofication will get queued up and delivered. The buckets include:

    * PREP (Preparatory) notifications are all delivered first, and help the
      user learn about things they can do to build a behavior.
    * CORE notifications are sent when the user has compelted the PREP actions.
      These help the user to keep working toward their goal
    * HELPER notifications are delivered if the user asks for more help.
      These are intended to help get you back on track or give an extra nudge.
    * CHECKUP notifications are delivered infrequently, and ask the user how
      they're doing or if they want to re-start the helper/core notifications.

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

    # We group Action Types into "buckets" that determine the group of
    # notifications they'll be sent over time.
    PREP = 'prep'
    CORE = 'core'
    HELPER = 'helper'
    CHECKUP = 'checkup'
    HELPERS = [STARTER, TINY, RESOURCE, NOW, LATER]

    # A mapping from action_type to bucket
    BUCKET_MAPPING = {
        REINFORCING: PREP,
        ENABLING: CORE,
        SHOWING: CORE,
        STARTER: HELPER,
        TINY: HELPER,
        RESOURCE: HELPER,
        NOW: HELPER,
        LATER: HELPER,
        ASKING: CHECKUP,
    }

    # A mapping of current -> next bucket. We have the buckets, but we need
    # a way to determine their progression. When a user "positively" completes
    # all actions within a bucket, we move on to the next. See the
    # progress.UserCompletedAction model.
    #
    # PREP -> CORE -> (HELPER only if they ask?) -> CHECKUP
    BUCKET_ORDER = [PREP, CORE, HELPER, CHECKUP]
    BUCKET_PROGRESSION = {
        PREP: CORE,
        CORE: CHECKUP,
        HELPER: CHECKUP,
        CHECKUP: None,
        None: PREP,
    }

    BUCKET_CHOICES = (  # The notification buckets.
        (PREP, 'Preparatory'),
        (CORE, 'Core'),
        (HELPER, 'Helper'),
        (CHECKUP, 'Checkup'),
    )

    ACTION_TYPE_CHOICES = (
        (REINFORCING, 'Reinforcing'),
        (ENABLING, 'Enabling'),
        (SHOWING, 'Showing'),
        (STARTER, 'Starter Step'),
        (TINY, 'Tiny Version'),
        (RESOURCE, 'Resource Notification'),
        (NOW, 'Do it now'),
        (LATER, 'Do it later'),
        (ASKING, 'Checkup Notification'),
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

    behavior = models.ForeignKey(Behavior, verbose_name="behavior")
    action_type = models.CharField(
        max_length=32,
        default=SHOWING,
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
    priority = models.PositiveIntegerField(
        default=LOW,
        choices=PRIORITY_CHOICES,
        help_text="Priority determine how notifications get queued for delivery"
    )
    bucket = models.CharField(
        max_length=32,
        blank=True,
        default=CORE,
        choices=BUCKET_CHOICES,
        help_text='The "bucket" from which this object is selected when '
                  'queueing up notifications.'
    )
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
        ordering = ['sequence_order', 'action_type', 'title']
        verbose_name = "Action"
        verbose_name_plural = "Actions"
        # add_action, change_action, delete_action are created by default.
        permissions = (
            ("view_action", "Can view Actions"),
            ("decline_action", "Can Decline Actions"),
            ("publish_action", "Can Publish Actions"),
        )

    @classmethod
    def next_bucket(cls, bucket_progress):
        """This classmethod can be used to determine the next bucket from
        which actions should be delivered. It can be provided a bucket name
        or a dict of bucket progress values (see UserBehavior.bucket_progress).

        Usage:

            Action.next_bucket(Action.PREP) --> Action.CORE

        or:

            Action.next_behavior({Action.PREP: True}) --> Action.CORE

        """
        # If bucket_progress is actually the name of the bucket, then just
        # return the next bucket in the progression.
        # If bucket_progress is a dict, we'll get an 'unhashable type' error
        try:
            return cls.BUCKET_PROGRESSION[bucket_progress]
        except TypeError:
            pass

        # Othewise, we expect bucket progress to be a dict of bucket:completed
        # values, so we need to look up the order based on which ones have been
        # completed.
        result = None  # Which bucket is next
        result_index = -1  # the order in which the buckets should be completed.
        for bucket, completed in bucket_progress.items():
            bucket_index = cls.BUCKET_ORDER.index(bucket)
            if completed and bucket_index > result_index:
                result = bucket
                result_index = bucket_index
        return cls.BUCKET_PROGRESSION[result]

    @classmethod
    def _add_action_type_creation_urls_to_action(cls):
        """Add the get_create_ACTION_TYPE_action_url methods for all of the
        different action_type options that we currently have defined on the
        Action model.

        This method is called in the app's config, GoalsConfig.ready.

        """
        for action_type in cls.BUCKET_MAPPING.keys():
            func_name = 'get_create_{}_action_url'.format(action_type)
            func = _action_type_url_function(action_type)
            setattr(cls, func_name, classmethod(func))

    def __str__(self):
        return "{}".format(self.title)

    def _set_notification_text(self):
        if not self.notification_text:
            self.notification_text = self.title

    def _set_bucket(self):
        """Set this object's bucket based on it's action type."""
        self.bucket = self.BUCKET_MAPPING.get(self.action_type, self.CORE)

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
        self._set_bucket()
        self._set_notification_text()
        self._serialize_default_trigger()
        super().save(*args, **kwargs)
        self.remove_queued_messages()

    @property
    def behavior_title(self):
        """Return only the title for the related Behavior."""
        return self.behavior.title

    @property
    def behavior_description(self):
        """Return only the description for the related Behavior."""
        return self.behavior.description

    @property
    def order(self):
        return self.sequence_order

    @property
    def is_helper(self):
        return self.action_type in self.HELPERS

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
        that have selected the parent behavior."""

        # For everyone that's selected this action's parent Behavior:
        for ub in self.behavior.userbehavior_set.all():
            # Add this new action.
            ub.add_actions(action_id=self.id)
    objects = WorkflowManager()


# This is a signal that gets fired when an action is unpublished (i.e. reverted
# to a `draft` state. This is implemented as a signal, since we already have a
# signal handler that delete relevant GCM Messages and we want to do the same
# when an Action is unpublished.
_unpublished_args = ['sender', 'instance', 'using']  # same as post-delete
action_unpublished = django.dispatch.Signal(providing_args=_unpublished_args)
