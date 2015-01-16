from django.contrib import admin
from . import models


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'name', 'name_slug')
    prepopulated_fields = {"name_slug": ("name", )}
admin.site.register(models.Category, CategoryAdmin)


class InterestAdmin(admin.ModelAdmin):
    list_display = ('order', 'name',)
admin.site.register(models.Interest, InterestAdmin)


class ActionAdmin(admin.ModelAdmin):
    list_display = ('order', 'name')
admin.site.register(models.Action, ActionAdmin)


class CustomReminderAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'time', 'frequency')
admin.site.register(models.CustomReminder, CustomReminderAdmin)


class SelectedActionAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'date_selected')
admin.site.register(models.SelectedAction, SelectedActionAdmin)


class ActionTakenAdmin(admin.ModelAdmin):
    list_display = ('user', 'selected_action', 'date_completed')
admin.site.register(models.ActionTaken, ActionTakenAdmin)
