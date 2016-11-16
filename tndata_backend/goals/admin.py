import urllib
from pprint import pformat

from django.contrib import admin
from django.contrib.messages import ERROR
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.template.defaultfilters import timesince
from django.utils.text import mark_safe

import tablib
from django_fsm import TransitionNotAllowed
from utils.admin import UserRelatedModelAdmin

from . import models


class ContentWorkflowAdmin(admin.ModelAdmin):
    """This class adds action methods for changing the state of content."""

    actions = [
        'set_draft', 'set_review', 'set_declined', 'set_published',
        'publish_children',
    ]

    def _transition_to(self, request, queryset, method, message):
        try:
            with transaction.atomic():
                for obj in queryset:
                    getattr(obj, method)()  # Call the transition method.
                    obj.save(updated_by=request.user)
            self.message_user(request, message)
        except TransitionNotAllowed as err:
            self.message_user(request, err, level=ERROR)

    def set_draft(self, request, queryset):
        self._transition_to(request, queryset, "draft", "Items marked Draft")
    set_draft.short_description = "Mark as Draft"

    def set_review(self, request, queryset):
        self._transition_to(request, queryset, "review", "Items submitted for review")
    set_review.short_description = "Submit for Review"

    def set_declined(self, request, queryset):
        self._transition_to(request, queryset, "decline", "Items Declined")
    set_declined.short_description = "Decline Items"

    def set_published(self, request, queryset):
        self._transition_to(request, queryset, "publish", "Items Published")
    set_published.short_description = "Publish"

    def publish_children(self, request, queryset):
        count = 0  # Track total number of items published.

        # publish the selected objects:
        for obj in queryset:
            if obj.is_draft or obj.is_pending:
                obj.publish()
                obj.save()
                count += 1

        # Now, publish all the children
        children = [obj.publish_children() for obj in queryset]
        children = [val for sublist in children for val in sublist]
        count += len(children)

        # and the children's children
        while len(children) > 0:
            children = [obj.publish_children() for obj in children]
            children = [val for sublist in children for val in sublist]
            count += len(children)
        self.message_user(request, "Published {} objects.".format(count))
    publish_children.short_description = "Publish selected item and all child content"


class CategoryAdmin(ContentWorkflowAdmin):
    list_display = (
        'title', 'state', 'updated', 'created_on', 'group',
        'packaged_content', 'selected_by_default',
    )
    search_fields = ['title', 'description', 'notes', 'id']
    list_filter = (
        'state', 'packaged_content', 'selected_by_default',
        'hidden_from_organizations', 'grouping',
    )
    prepopulated_fields = {"title_slug": ("title", )}
    raw_id_fields = (
        'organizations', 'hidden_from_organizations', 'contributors',
        'updated_by', 'created_by'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions.append('delete_children')

    def updated(self, obj):
        return "{} ago".format(timesince(obj.updated_on))

    def group(self, obj):
        return "{} / {}".format(obj.grouping, obj.grouping_name)

    def delete_children(self, request, queryset):
        # publish the selected objects:
        categories_to_delete = set(queryset.values_list('id', flat=True))

        # Find all the child goals that are in no other categories.
        goals = models.Goal.objects.filter(categories__in=categories_to_delete)
        goals_to_delete = set()
        for goal in goals:
            parents = set(goal.categories.values_list('id', flat=True))
            if parents.issubset(categories_to_delete):
                goals_to_delete.add(goal.id)

        # Remove the Actions that are in no other goals.
        actions = models.Action.objects.filter(goals__in=goals_to_delete)
        actions_to_delete = set()
        for action in actions:
            parents = set(action.goals.values_list('id', flat=True))
            if parents.issubset(goals_to_delete):
                actions_to_delete.add(action.id)

        # Build a confirmation message
        msg = "Deleted {a} Actions, {g} Goals, and {c} Categories."
        msg = msg.format(
            a=actions.count(),
            g=len(goals_to_delete),
            c=len(categories_to_delete),
        )

        # NOW, delete stuff.
        models.Action.objects.filter(id__in=actions_to_delete).delete()
        models.Goal.objects.filter(id__in=goals_to_delete).delete()
        queryset.delete()  # the categories.
        self.message_user(request, msg)

    delete_children.short_description = "Delete selected item and all child content"
admin.site.register(models.Category, CategoryAdmin)


class ArrayFieldListFilter(admin.SimpleListFilter):
    """An admin list filter based on the values from a model's `keywords`
    ArrayField. For more info, see the django docs:

    https://docs.djangoproject.com/en/1.8/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_filter

    """
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = "Keywords"

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'keywords'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        keywords = models.Goal.objects.values_list("keywords", flat=True)
        keywords = [(kw, kw) for sublist in keywords for kw in sublist if kw]
        keywords = sorted(set(keywords))
        return keywords

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        lookup = self.value()
        if lookup:
            queryset = queryset.filter(keywords__contains=[lookup])
        return queryset


class CategoryListFilter(admin.SimpleListFilter):
    """Admin Filter that lists categories in alpha-order by title."""
    title = "Category"
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        return models.Category.objects.values_list('id', 'title').order_by('title')

    def queryset(self, request, queryset):
        category_id = self.value()
        if category_id:
            queryset = queryset.filter(categories__id=category_id)
        return queryset


class GoalAdmin(ContentWorkflowAdmin):
    list_display = (
        'title', 'sequence_order', 'state', 'in_categories', 'created_by',
        'created_on', 'updated_on',
    )
    search_fields = [
        'title', 'subtitle', 'description', 'more_info', 'keywords', 'id'
    ]
    list_filter = ('state', ArrayFieldListFilter, CategoryListFilter)
    prepopulated_fields = {"title_slug": ("title", )}
    filter_horizontal = ('categories', )
    actions = ['add_keywords', ]
    raw_id_fields = ('updated_by', 'created_by')

    def add_keywords(self, request, queryset):
        ids = "+".join(str(g.id) for g in queryset)
        args = urllib.parse.urlencode({'ids': ids})
        url = reverse('goals:batch-assign-keywords')
        return HttpResponseRedirect("{0}?{1}".format(url, args))
    add_keywords.description = "Assign Keywords"

    def in_categories(self, obj):
        return ", ".join(sorted([cat.title for cat in obj.categories.all()]))
admin.site.register(models.Goal, GoalAdmin)


class TriggerAdmin(UserRelatedModelAdmin):
    list_display = (
        'combined', 'email', 'time', 'trigger_date', 'stop_on_complete',
        'start_when_selected', 'relative', 'dynamic', 'next',
        'rrule'
    )
    prepopulated_fields = {"name_slug": ("name", )}
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'name',
    ]
    raw_id_fields = ('user', )

    def rrule(self, obj):
        return obj.serialized_recurrences()

    def dynamic(self, obj):
        return obj.is_dynamic
    dynamic.boolean = True

    def relative(self, obj):
        if obj.relative_value:
            return '{} {}'.format(obj.relative_value, obj.relative_units)
        return ''
    relative.admin_order_field = 'relative_value'

    def email(self, obj):
        if obj.user:
            return obj.user.email
        return ''
    email.admin_order_field = 'user.email'

    def combined(self, obj):
        return str(obj)
    combined.admin_order_field = 'name'

admin.site.register(models.Trigger, TriggerAdmin)


class GoalListFilter(admin.SimpleListFilter):
    """Admin Filter that lists goals in alpha-order by title."""
    title = "By Goal"
    parameter_name = 'goal'

    def lookups(self, request, model_admin):
        return models.Goal.objects.values_list('id', 'title').order_by('title')

    def queryset(self, request, queryset):
        goal_id = self.value()
        if goal_id:
            queryset = queryset.filter(goals__id=goal_id)
        return queryset


class ActionCategoryListFilter(CategoryListFilter):
    """Filters actions by their parent goal's category."""
    def queryset(self, request, queryset):
        category_id = self.value()
        if category_id:
            queryset = queryset.filter(goals__categories__id=category_id)
        return queryset


class ActionTriggerListFilter(admin.SimpleListFilter):
    title = "Trigger"
    parameter_name = 'trigger'

    def lookups(self, request, model_admin):
        return (
            ('dynamic', 'Dynamic'),
            ('time', 'Time of Day Only'),
            ('freq', 'Frequency Only'),
            ('advanced', 'Advanced Only'),
            ('none', 'No Trigger'),
            # ('time', 'Dynamic Time + Advanced'),
            # ('freq', 'Dynamic Frequency + Advanced')
        )

    def queryset(self, request, queryset):
        lookup = self.value()
        if lookup == 'dynamic':
            queryset = queryset.filter(
                default_trigger__time_of_day__isnull=False,
                default_trigger__frequency__isnull=False,
            )
        elif lookup == 'advanced':
            queryset = queryset.filter(
                default_trigger__time_of_day__isnull=True,
                default_trigger__frequency__isnull=True,
            )
        elif lookup == 'time':
            queryset = queryset.filter(
                default_trigger__time_of_day__isnull=False,
                default_trigger__frequency__isnull=True,
            )
        elif lookup == 'freq':
            queryset = queryset.filter(
                default_trigger__time_of_day__isnull=True,
                default_trigger__frequency__isnull=False,
            )
        elif lookup == 'none':
            queryset = queryset.filter(
                default_trigger__isnull=True,
            )
        return queryset


class ActionAdmin(ContentWorkflowAdmin):
    list_display = (
        'title', 'sequence_order', 'notification_text', 'state', 'action_type',
        'selected_by_users',
    )
    search_fields = [
        'id', 'title', 'source_notes', 'notes', 'more_info', 'description',
        'notification_text', 'goals__title',
    ]
    list_filter = (
        'state', ActionTriggerListFilter, 'action_type', 'priority',
        'external_resource_type', ActionCategoryListFilter,
    )
    prepopulated_fields = {"title_slug": ("title", )}
    raw_id_fields = ('goals', 'default_trigger', 'updated_by', 'created_by')

    def selected_by_users(self, obj):
        return models.UserAction.objects.filter(action=obj).count()

admin.site.register(models.Action, ActionAdmin)


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_on', 'updated_on')
    search_fields = ['name', ]
    prepopulated_fields = {"name_slug": ("name", )}
    raw_id_fields = ('members', 'staff', 'admins')
admin.site.register(models.Organization, OrganizationAdmin)


class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'created_on', 'updated_on')
    search_fields = ['name', 'organization__name']
    prepopulated_fields = {"name_slug": ("name", )}
    raw_id_fields = ('organization', 'members', 'categories', 'auto_enrolled_goals')
admin.site.register(models.Program, ProgramAdmin)


class UserCategoryAdmin(UserRelatedModelAdmin):
    list_display = (
        'user_email', 'category', 'created_on', 'accepted', 'enrolled',
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'category__title', 'category__id', 'id',
    )
    raw_id_fields = ("user", "category")

    def accepted(self, obj):
        values = obj.category.packageenrollment_set.filter(user=obj.user)
        return all(values.values_list("accepted", flat=True))
    accepted.boolean = True

    def enrolled(self, obj):
        items = obj.category.packageenrollment_set.filter(user=obj.user)
        results = [item.enrolled_on.isoformat() for item in items]
        return ", ".join(results)

admin.site.register(models.UserCategory, UserCategoryAdmin)


class UserGoalAdmin(UserRelatedModelAdmin):
    list_display = (
        'user_email', 'goal', 'categories', 'completed', 'engagement_15_days',
        'engagement_30_days', 'engagement_60_days', 'engagement_rank',
    )
    list_filter = ('completed', 'goal__categories', )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'goal__title', 'goal__id', 'id',
    )
    raw_id_fields = ("user", "goal")

    def categories(self, obj):
        cats = set()
        for title in obj.goal.categories.values_list("title", flat=True):
            cats.add(title)
        return ", ".join(cats)
admin.site.register(models.UserGoal, UserGoalAdmin)


class UACategoryListFilter(admin.SimpleListFilter):
    title = "Primary Category"
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        qs = models.Category.objects.all()
        return qs.values_list('id', 'title').order_by('title')

    def queryset(self, request, queryset):
        category_id = self.value()
        if category_id:
            queryset = queryset.filter(primary_category__id=category_id)
        return queryset


class UserActionCompletedListFilter(admin.SimpleListFilter):
    title = "Completed"
    parameter_name = 'completed'

    def lookups(self, request, model_admin):
        return ((1, 'Yes'), (0, 'No'))

    def queryset(self, request, queryset):
        completed = self.value()
        if completed is None:
            return queryset
        else:
            completed = bool(int(completed))

        if completed:
            queryset = queryset.filter(
                usercompletedaction__isnull=False,
                usercompletedaction__state=models.UserCompletedAction.COMPLETED
            )
        else:
            states = [
                models.UserCompletedAction.UNSET,
                models.UserCompletedAction.UNCOMPLETED,
                models.UserCompletedAction.DISMISSED,
                models.UserCompletedAction.SNOOZED,
            ]
            queryset = queryset.filter(
                Q(usercompletedaction__isnull=True) |
                Q(
                    usercompletedaction__isnull=False,
                    usercompletedaction__state__in=states
                )
            )
            queryset = queryset.exclude(usercompletedaction__state='completed')
        return queryset


class UserActionAdmin(UserRelatedModelAdmin):
    list_display = (
        'user_email', 'next_trigger_date', 'notification',
        'sequence_order', 'action', 'primary_goal',
        'primary_category', 'completed',
    )
    list_filter = (
        UserActionCompletedListFilter,
        UACategoryListFilter,
        'primary_goal'
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'action__id', 'action__title', 'action__notification_text', 'id',
    )
    readonly_fields = ['prev_trigger_date', 'next_trigger_date']
    raw_id_fields = ("user", "action", 'custom_trigger', "primary_goal")

    def sequence_order(self, obj):
        return obj.action.sequence_order

    def completed(self, obj):
        return obj.completed
    completed.boolean = True

    def action_state(self, obj):
        return obj.action.state

    def notification(self, obj):
        return obj.action.notification_text
admin.site.register(models.UserAction, UserActionAdmin)


def tablib_export_user_completed_actions(modeladmin, request, queryset):
    """Adapted from django_tablib, which hasn't been upgraded in a while :( """
    data = tablib.Dataset()
    for uca in queryset:
        # Ensure our dates are serialized.
        completed_on = uca.created_on.strftime("%c")
        action_added_on = uca.useraction.created_on.strftime("%c")

        data.append([
            uca.user.email,
            uca.action.title,
            uca.state,
            completed_on,
            action_added_on,
        ])

    data.headers = ['Email', 'Action', 'State', 'Saved On', 'Action Adopted']
    filename = 'completed_actions.csv'
    response = HttpResponse(data.csv, content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response
tablib_export_user_completed_actions.short_description = "Export Data as a CSV File"


class UCACategoryListFilter(admin.SimpleListFilter):
    title = "Primary Category"
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        qs = models.Category.objects.all()
        return qs.values_list('id', 'title').order_by('title')

    def queryset(self, request, queryset):
        category_id = self.value()
        if category_id:
            queryset = queryset.filter(
                useraction__primary_category__id=category_id)
        return queryset


class UserCompletedActionAdmin(UserRelatedModelAdmin):
    list_display = (
        'user_email', 'action', 'state', 'updated_on',
        'primary_goal', 'primary_category',
    )
    list_filter = ('state', UCACategoryListFilter, )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'action__id', 'action__title',
    )
    raw_id_fields = ("user", "action", "useraction")
    actions = [tablib_export_user_completed_actions]

    def primary_goal(self, obj):
        return obj.useraction.primary_goal
    primary_goal.admin_order_field = 'useraction__primary_goal__title'

    def primary_category(self, obj):
        return obj.useraction.primary_category
    primary_category.admin_order_field = 'useraction__primary_category__title'

admin.site.register(models.UserCompletedAction, UserCompletedActionAdmin)


class PackageEnrollmentAdmin(UserRelatedModelAdmin):
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'category__title', 'category__id', 'goals__title',
    )
    list_display = (
        'user_email', 'full_name', 'category', 'accepted',
        'prevent_custom_triggers', 'enrolled_by', 'enrolled_on',
    )
    list_filter = ('prevent_custom_triggers', 'category')
    raw_id_fields = ("user", 'enrolled_by', 'goals')

admin.site.register(models.PackageEnrollment, PackageEnrollmentAdmin)


class CustomActionInline(admin.TabularInline):
    """Inline action form for Custom Goals. This is here so we can create a
    custom goal + actions in the admin all at once."""
    model = models.CustomAction
    raw_id_fields = ('user', 'custom_trigger')


class CustomGoalAdmin(UserRelatedModelAdmin):
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'title',
    )
    list_display = ('title', 'full_name', 'created_on')
    raw_id_fields = ('user', )
    inlines = [CustomActionInline]

    def full_name(self, obj):
        return obj.user.get_full_name() or obj.user.email
    full_name.admin_order_field = 'user'
admin.site.register(models.CustomGoal, CustomGoalAdmin)


class CustomActionAdmin(UserRelatedModelAdmin):
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'title', 'customgoal__title', 'notification_text', 'goal__title',
    )
    list_display = (
        'user_email', 'title', 'customgoal', 'goal',
        'prev_trigger_date', 'next_trigger_date', 'created_on',
    )
    raw_id_fields = ('user', 'goal', 'customgoal', 'custom_trigger')
    readonly_fields = (
        'next_trigger_date', 'prev_trigger_date',
        'updated_on', 'created_on',
    )
admin.site.register(models.CustomAction, CustomActionAdmin)


class CustomActionFeedbackAdmin(UserRelatedModelAdmin):
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'customgoal__title', 'goal__title', 'customaction__title', 'text'
    )
    list_display = (
        'user_email', 'customgoal', 'goal', 'customaction', 'text', 'created_on'
    )
    raw_id_fields = ('user', 'goal', 'customgoal', 'customaction')
admin.site.register(models.CustomActionFeedback, CustomActionFeedbackAdmin)


class UserCompletedCustomActionAdmin(UserRelatedModelAdmin):
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'customaction__title', 'customgoal__title', 'state'
    )
    list_display = ('customgoal', 'customaction', 'created_on')
    list_filter = ('state', )
    raw_id_fields = ('user', 'customaction', 'customgoal')
admin.site.register(models.UserCompletedCustomAction, UserCompletedCustomActionAdmin)


class DailyProgressAdmin(UserRelatedModelAdmin):
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
    )
    list_display = (
        'user', 'actions_total', 'engagement_15_days', 'engagement_30_days',
        'engagement_60_days', 'created_on',
    )
    raw_id_fields = ('user', )
    exclude = ('goal_status', )
    readonly_fields = (
        'actions_total', 'actions_completed', 'actions_snoozed',
        'actions_dismissed', 'customactions_total', 'customactions_completed',
        'customactions_snoozed', 'customactions_dismissed',
        'goal_status_details', 'engagement_15_days', 'engagement_30_days',
        'engagement_60_days', 'updated_on', 'created_on'
    )

    def goal_status_details(self, obj):
        return mark_safe("<pre>{0}</pre>".format(pformat(obj.goal_status)))

admin.site.register(models.DailyProgress, DailyProgressAdmin)
