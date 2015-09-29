from django.contrib import admin
from django.contrib.messages import ERROR
from django.db import IntegrityError, transaction
from django.http import HttpResponse

import tablib
from django_fsm import TransitionNotAllowed
from utils.admin import UserRelatedModelAdmin

from . import models


class ContentWorkflowAdmin(admin.ModelAdmin):
    """This class adds action methods for changing the state of content."""

    actions = ['set_draft', 'set_review', 'set_declined', 'set_published']

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


class CategoryAdmin(ContentWorkflowAdmin):
    list_display = (
        'title', 'title_slug', 'state', 'order', 'get_absolute_icon',
        'created_by', 'created_on', 'updated_by', 'updated_on',
    )
    search_fields = ['title', 'description', 'notes']
    list_filter = ('state', )
    prepopulated_fields = {"title_slug": ("title", )}
    raw_id_fields = ('updated_by', 'created_by')

admin.site.register(models.Category, CategoryAdmin)


class GoalAdmin(ContentWorkflowAdmin):
    list_display = (
        'title', 'title_slug', 'state', 'in_categories', 'get_absolute_icon',
        'created_by', 'created_on', 'updated_by', 'updated_on',
    )
    search_fields = ['title', 'subtitle', 'description', 'outcome', 'keywords']
    list_filter = ('state', )
    prepopulated_fields = {"title_slug": ("title", )}
    filter_horizontal = ('categories', )
    raw_id_fields = ('updated_by', 'created_by')

    def in_categories(self, obj):
        return ", ".join(sorted([cat.title for cat in obj.categories.all()]))

admin.site.register(models.Goal, GoalAdmin)


class TriggerAdmin(UserRelatedModelAdmin):
    list_display = (
        'combined', 'email', 'trigger_type', 'next', 'serialized_recurrences',
        'location',
    )
    prepopulated_fields = {"name_slug": ("name", )}
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'name', 'location',
    ]
    raw_id_fields = ('user', )

    def email(self, obj):
        if obj.user:
            return obj.user.email
        return ''

    def combined(self, obj):
        return str(obj)

admin.site.register(models.Trigger, TriggerAdmin)


class BehaviorAdmin(ContentWorkflowAdmin):
    list_display = (
        'title', 'state', 'num_actions', 'selected_by_users', 'in_categories',
        'in_goals', 'get_absolute_icon', 'get_absolute_image',
        'created_by', 'created_on', 'updated_by', 'updated_on',
    )
    search_fields = [
        'title', 'source_notes', 'notes', 'more_info', 'description',
        'case', 'outcome', 'notification_text',
    ]
    list_filter = ('state', )
    prepopulated_fields = {"title_slug": ("title", )}
    raw_id_fields = ('updated_by', 'created_by')
    filter_horizontal = ('goals', )
    actions = ['convert_to_goal']

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


class ActionAdmin(ContentWorkflowAdmin):
    list_display = (
        'title', 'state', 'selected_by_users', 'behavior', 'sequence_order',
        'get_absolute_icon', 'get_absolute_image',
        'created_by', 'created_on', 'updated_by', 'updated_on',
    )
    search_fields = [
        'title', 'source_notes', 'notes', 'more_info', 'description',
        'case', 'outcome', 'notification_text',
    ]
    list_filter = ('state', )
    prepopulated_fields = {"title_slug": ("title", )}
    raw_id_fields = ('behavior', 'updated_by', 'created_by')
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
                        case=action.case,
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
        'category__title', 'category__id'
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
        'goal__title', 'goal__id',
    )
    raw_id_fields = ("user", "goal")

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
        'behavior__id', 'behavior__title',
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
        'user_email', 'user_first', 'user_last', 'notification', 'action',
        'action_state', 'primary_goal', 'categories', 'custom_triggers_allowed',
        'created_on',
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'action__id', 'action__title', 'action__notification_text',
    )
    raw_id_fields = ("user", "action")

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


class BehaviorProgressAdmin(UserRelatedModelAdmin):
    list_display = (
        'user', 'behavior', 'status', 'reported_on'
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
    )
    raw_id_fields = ("user", "user_behavior")

admin.site.register(models.BehaviorProgress, BehaviorProgressAdmin)


class GoalProgressAdmin(UserRelatedModelAdmin):
    list_display = (
        'user', 'goal', 'current_total', 'max_total',
        'current_score', 'text_glyph', 'reported_on'
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'goal__id', 'goal__title',
    )
    raw_id_fields = ("user", "goal")

admin.site.register(models.GoalProgress, GoalProgressAdmin)


class CategoryProgressAdmin(UserRelatedModelAdmin):
    list_display = (
        'user', 'category', 'current_score', 'text_glyph', 'reported_on'
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'category__id', 'category__title',
    )
    raw_id_fields = ("user", 'category')

admin.site.register(models.CategoryProgress, CategoryProgressAdmin)


class PackageEnrollmentAdmin(UserRelatedModelAdmin):
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'category__title', 'goals__title',
    )
    list_display = (
        'user_email', 'user_first', 'user_last', 'accepted', 'enrolled_by',
        'enrolled_on', 'category',
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'category__id', 'category__title',
    )
    raw_id_fields = ("user", 'enrolled_by', 'goals')

admin.site.register(models.PackageEnrollment, PackageEnrollmentAdmin)
