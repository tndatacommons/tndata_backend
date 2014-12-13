from django.contrib import admin
from . import models


class GoalAdmin(admin.ModelAdmin):
    list_display = ('rank', 'name')
admin.site.register(models.Goal, GoalAdmin)


class BehaviorAdmin(admin.ModelAdmin):
    list_display = ('goal', 'name')
admin.site.register(models.Behavior, BehaviorAdmin)


class BehaviorStepAdmin(admin.ModelAdmin):
    list_display = ('goal', 'behavior', 'name', 'reminder_type')
admin.site.register(models.BehaviorStep, BehaviorStepAdmin)


class CustomReminderAdmin(admin.ModelAdmin):
    list_display = ('user', 'behavior_step', 'time', 'repeat', 'location', 'reminder_type')
admin.site.register(models.CustomReminder, CustomReminderAdmin)


class ChosenBehaviorAdmin(admin.ModelAdmin):
    list_display = ('user', 'goal', 'behavior', 'date_selected')
admin.site.register(models.ChosenBehavior, ChosenBehaviorAdmin)


class CompletedBehaviorStepAdmin(admin.ModelAdmin):
    list_display = ('user', 'goal', 'behavior', 'behavior_step', 'date_completed')
admin.site.register(models.CompletedBehaviorStep, CompletedBehaviorStepAdmin)
