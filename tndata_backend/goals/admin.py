import urllib
from pprint import pformat

from django.contrib import admin
from django.contrib.messages import ERROR
from django.core.urlresolvers import reverse
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseRedirect
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
        print("Published:\n- {}".format("\n- ".join([str(obj) for obj in children])))

        # and the children's children
        while len(children) > 0:
            children = [obj.publish_children() for obj in children]
            children = [val for sublist in children for val in sublist]
            count += len(children)
            print("Published:\n- {}".format("\n- ".join([str(obj) for obj in children])))
        print("Count: {}".format(count))
        self.message_user(request, "Published {} objects.".format(count))
    publish_children.short_description = "Publish selected item and all child content"


class CategoryAdmin(ContentWorkflowAdmin):
    list_display = (
        'title', 'state', 'created_by', 'updated_on', 'created_on',
        'packaged_content', 'selected_by_default',
    )
    search_fields = ['title', 'description', 'notes', 'id']
    list_filter = ('state', 'packaged_content', 'selected_by_default')
    prepopulated_fields = {"title_slug": ("title", )}
    raw_id_fields = ('updated_by', 'created_by')

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
    title = "By Category"
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
        'title', 'state', 'in_categories', 'created_by',
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


class BehaviorCategoryListFilter(CategoryListFilter):
    """Filters behaviors by their parent goal's category."""
    def queryset(self, request, queryset):
        category_id = self.value()
        if category_id:
            queryset = queryset.filter(goals__categories__id=category_id)
        return queryset


class BehaviorAdmin(ContentWorkflowAdmin):
    list_display = (
        'title', 'state', 'in_goals', 'updated_on',
        'has_prep_actions', 'num_actions', 'selected_by_users',
    )
    search_fields = [
        'title', 'source_notes', 'notes', 'more_info', 'description', 'id',
    ]
    list_filter = ('state', BehaviorCategoryListFilter, GoalListFilter)
    prepopulated_fields = {"title_slug": ("title", )}
    raw_id_fields = ('updated_by', 'created_by')
    filter_horizontal = ('goals', )
    actions = ['convert_to_goal']

    def has_prep_actions(self, obj):
        return obj.action_buckets_prep > 0
    has_prep_actions.boolean = True
    has_prep_actions.admin_order_field = 'action_buckets_prep'

    def selected_by_users(self, obj):
        return models.UserBehavior.objects.filter(behavior=obj).count()

    def num_actions(self, obj):
        return obj.action_set.count()

    def in_categories(self, obj):
        return ", ".join(sorted([cat.title for cat in obj.categories.all()]))

    def in_goals(self, obj):
        return ", ".join(sorted([g.title for g in obj.goals.all()]))

    def convert_to_goal(self, request, queryset):
        """Converts the Behavior into a Goal. The categories that were associated
        with the Behavior's Parent Goal and now associated with the new Goal
        created from the behavior."""

        try:
            with transaction.atomic():
                num_objects = queryset.count()
                for behavior in queryset:
                    # get the parent goals's list of categories
                    categories = list(behavior.categories)

                    # create the new goal
                    goal = models.Goal.objects.create(
                        title=behavior.title,
                        title_slug=behavior.title_slug,
                        subtitle='',
                        notes=behavior.notes,
                        more_info=behavior.more_info,
                        description=behavior.description,
                        outcome=behavior.outcome,
                        state=behavior.state,
                        created_by=request.user,
                        updated_by=request.user,
                    )
                    # add in the goals
                    for cat in categories:
                        goal.categories.add(cat)
                    goal.save()

            # When the goals have been created, delete the set of Behaviors.
            with transaction.atomic():
                # Call each item's .delete() method so the post_delete
                # signal gets sent... which will remove the icon/image
                for obj in queryset:
                    obj.delete()

            msg = "Converted {0} Behaviors into Goals".format(num_objects)
            self.message_user(request, msg)
        except IntegrityError:
            msg = (
                "There was an error converting Behaviors. All changes have been "
                "rolled back."
            )
            self.message_user(request, msg, level=ERROR)

admin.site.register(models.Behavior, BehaviorAdmin)


class ActionCategoryListFilter(CategoryListFilter):
    """Filters actions by their parent behavior's parent goal's category."""
    def queryset(self, request, queryset):
        category_id = self.value()
        if category_id:
            queryset = queryset.filter(behavior__goals__categories__id=category_id)
        return queryset


class ActionAdmin(ContentWorkflowAdmin):
    list_display = (
        'title', 'notification_text', 'state', 'action_type',
        'selected_by_users',
    )
    search_fields = [
        'id', 'title', 'source_notes', 'notes', 'more_info', 'description',
        'notification_text', 'behavior__title',
    ]
    list_filter = (
        'state', 'bucket', 'action_type', 'priority', ActionCategoryListFilter
    )
    prepopulated_fields = {"title_slug": ("title", )}
    raw_id_fields = ('behavior', 'default_trigger', 'updated_by', 'created_by')
    actions = ['convert_to_behavior']

    def selected_by_users(self, obj):
        return models.UserAction.objects.filter(action=obj).count()

    def convert_to_behavior(self, request, queryset):
        """Converts the Action into a Behavior. The goals that were associated
        with the Action's Parent behavior and now associated with the Behavior
        created from the action."""

        try:
            with transaction.atomic():
                num_actions = queryset.count()
                for action in queryset:
                    # get the parent behavior's list of goals
                    goals = list(action.behavior.goals.all())

                    # create the new behavior
                    behavior = models.Behavior.objects.create(
                        title=action.title,
                        title_slug=action.title_slug,
                        source_link=action.source_link,
                        source_notes=action.source_notes,
                        notes=action.notes,
                        more_info=action.more_info,
                        description=action.description,
                        outcome=action.outcome,
                        external_resource=action.external_resource,
                        default_trigger=action.default_trigger,
                        notification_text=action.notification_text,
                        state=action.state,
                        created_by=request.user,
                        updated_by=request.user,
                    )
                    # add in the goals
                    for g in goals:
                        behavior.goals.add(g)
                    behavior.save()

            # Once all behavior's have been created, delete the Actions.
            with transaction.atomic():
                # Call each item's .delete() method so the post_delete
                # signal gets sent... which will remove the icon/image
                for obj in queryset:
                    obj.delete()

            msg = "Converted {0} Actions into Behaviors".format(num_actions)
            self.message_user(request, msg)
        except IntegrityError:
            msg = (
                "There was an error converting Actions. All changes have been "
                "rolled back."
            )
            self.message_user(request, msg, level=ERROR)

admin.site.register(models.Action, ActionAdmin)


class UserCategoryAdmin(UserRelatedModelAdmin):
    list_display = (
        'user_email', 'user_first', 'user_last', 'user', 'category',
        'created_on', 'accepted', 'enrolled',
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'category__title', 'category__id', 'id',
    )
    raw_id_fields = ("user", "category")

    def accepted(self, obj):
        values = obj.category.packageenrollment_set.filter(user=obj.user)
        return all(values.values_list("accepted", flat=True))

    def enrolled(self, obj):
        items = obj.category.packageenrollment_set.filter(user=obj.user)
        results = [item.enrolled_on.isoformat() for item in items]
        return ", ".join(results)

admin.site.register(models.UserCategory, UserCategoryAdmin)


class UserGoalAdmin(UserRelatedModelAdmin):
    list_display = (
        'user_email', 'user_first', 'user_last', 'user', 'goal',
        'categories', 'created_on'
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'goal__title', 'goal__id', 'id',
    )
    raw_id_fields = ("user", "goal")
    readonly_fields = [
        'serialized_goal', 'serialized_user_behaviors',
        'serialized_user_categories', 'serialized_primary_category',
    ]

    def categories(self, obj):
        cats = set()
        for title in obj.goal.categories.values_list("title", flat=True):
            cats.add(title)
        return ", ".join(cats)

admin.site.register(models.UserGoal, UserGoalAdmin)


class UserBehaviorAdmin(UserRelatedModelAdmin):
    list_display = (
        'user_email', 'user_first', 'user_last', 'behavior', 'categories',
        'custom_trigger', 'created_on',
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'behavior__id', 'behavior__title', 'id',
    )
    raw_id_fields = ("user", "behavior")

    def categories(self, obj):
        cats = set()
        for g in obj.behavior.goals.all():
            for title in g.categories.values_list("title", flat=True):
                cats.add(title)
        return ", ".join(cats)

admin.site.register(models.UserBehavior, UserBehaviorAdmin)


class UserActionAdmin(UserRelatedModelAdmin):
    list_display = (
        'user_email', 'prev_trigger_date', 'next_trigger_date',
        'notification', 'action', 'behavior', 'created_on',
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'action__id', 'action__title', 'action__notification_text', 'id',
    )
    readonly_fields = [
        'prev_trigger_date', 'next_trigger_date', 'serialized_action',
        'serialized_behavior', 'serialized_custom_trigger',
        'serialized_primary_goal', 'serialized_primary_category',
    ]
    raw_id_fields = ("user", "action", 'custom_trigger', "primary_goal")

    def behavior(self, obj):
        return obj.action.behavior.title
    behavior.admin_order_field = 'action__behavior_id'

    def action_state(self, obj):
        return obj.action.state

    def notification(self, obj):
        return obj.action.notification_text

    def categories(self, obj):
        cats = set()
        for g in obj.action.behavior.goals.all():
            for title in g.categories.values_list("title", flat=True):
                cats.add(title)
        return ", ".join(cats)

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


class UserCompletedActionAdmin(UserRelatedModelAdmin):
    list_display = (
        'user_email', 'user_first', 'user_last',
        'useraction', 'action', 'state', 'created_on', 'updated_on',
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'action__id', 'action__title',
    )
    list_filter = ('state', )
    raw_id_fields = ("user", "action", "useraction")
    actions = [tablib_export_user_completed_actions]

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
        'title', 'customgoal__title', 'notification_text'
    )
    list_display = ('title', 'customgoal', 'prev_trigger_date', 'next_trigger_date', 'created_on')
    raw_id_fields = ('user', 'customgoal', 'custom_trigger')
    readonly_fields = ('next_trigger_date', 'prev_trigger_date')
admin.site.register(models.CustomAction, CustomActionAdmin)


class CustomActionFeedbackAdmin(UserRelatedModelAdmin):
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'customgoal__title', 'customaction__title', 'text'
    )
    list_display = ('customgoal', 'customaction', 'text', 'created_on')
    raw_id_fields = ('user', 'customgoal', 'customaction')
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
    list_display = ('user', 'actions_total', 'behaviors_total', 'created_on')
    raw_id_fields = ('user', )
    exclude = ('behaviors_status', 'goal_status')
    readonly_fields = (
        'actions_total', 'actions_completed', 'actions_snoozed',
        'actions_dismissed', 'customactions_total', 'customactions_completed',
        'customactions_snoozed', 'customactions_dismissed', 'behaviors_total',
        'behaviors_status_details', 'goal_status_details', 'updated_on', 'created_on'
    )

    def behaviors_status_details(self, obj):
        return mark_safe("<pre>{0}</pre>".format(pformat(obj.behaviors_status)))

    def goal_status_details(self, obj):
        return mark_safe("<pre>{0}</pre>".format(pformat(obj.goal_status)))

admin.site.register(models.DailyProgress, DailyProgressAdmin)
