from django.contrib import admin
from . import models


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'title_slug', 'order', 'get_absolute_icon')
    search_fields = ['title', 'description', 'notes']
    prepopulated_fields = {"title_slug": ("title", )}

admin.site.register(models.Category, CategoryAdmin)


class GoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'title_slug', 'in_categories', 'get_absolute_icon')
    search_fields = ['title', 'subtitle', 'description', 'outcome']
    prepopulated_fields = {"title_slug": ("title", )}

    def in_categories(self, obj):
        return ", ".join(sorted([cat.title for cat in obj.categories.all()]))

admin.site.register(models.Goal, GoalAdmin)


class TriggerAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'trigger_type', 'frequency', 'time', 'date', 'location',
    )
    prepopulated_fields = {"name_slug": ("name", )}
admin.site.register(models.Trigger, TriggerAdmin)


class BehaviorAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'in_categories', 'in_goals', 'get_absolute_icon',
        'get_absolute_image'
    )
    search_fields = [
        'title', 'source_notes', 'notes', 'narrative_block', 'description',
        'case', 'outcome', 'notification_text',
    ]
    prepopulated_fields = {"title_slug": ("title", )}

    def in_categories(self, obj):
        return ", ".join(sorted([cat.title for cat in obj.categories.all()]))

    def in_goals(self, obj):
        return ", ".join(sorted([g.title for g in obj.goals.all()]))
admin.site.register(models.Behavior, BehaviorAdmin)


class ActionAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'behavior', 'sequence_order', 'get_absolute_icon',
        'get_absolute_image'
    )
    search_fields = [
        'title', 'source_notes', 'notes', 'narrative_block', 'description',
        'case', 'outcome', 'notification_text',
    ]
    prepopulated_fields = {"title_slug": ("title", )}
admin.site.register(models.Action, ActionAdmin)


class UserGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'goal', 'completed', 'completed_on', 'created_on')
    search_fields = ('user', 'goal', 'completed', 'completed_on', 'created_on')
admin.site.register(models.UserGoal, UserGoalAdmin)


class UserBehaviorAdmin(admin.ModelAdmin):
    list_display = ('user', 'behavior', 'completed', 'completed_on', 'created_on')
    search_fields = ('user', 'behavior', 'completed', 'completed_on', 'created_on')
admin.site.register(models.UserBehavior, UserBehaviorAdmin)


class UserActionAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'completed', 'completed_on', 'created_on')
    search_fields = ('user', 'action', 'completed', 'completed_on', 'created_on')
admin.site.register(models.UserAction, UserActionAdmin)
