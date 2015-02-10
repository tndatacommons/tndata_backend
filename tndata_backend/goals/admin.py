from django.contrib import admin
from . import models


class InterestGroupAdmin(admin.ModelAdmin):
    # DEPRECATED.
    list_display = ('name', 'name_slug')
admin.site.register(models.InterestGroup, InterestGroupAdmin)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_slug', 'contains_interests', 'order')
    prepopulated_fields = {"name_slug": ("name", )}

    def contains_interests(self, obj):
        return ", ".join(sorted([i.name for i in obj.interests]))
admin.site.register(models.Category, CategoryAdmin)


class InterestAdmin(admin.ModelAdmin):
    list_display = ('name', 'in_category', 'order')
    list_display_links = ('order', 'name')
    prepopulated_fields = {"name_slug": ("name", )}

    def in_category(self, obj):
        return ", ".join(sorted([cat.name for cat in obj.categories.all()]))
admin.site.register(models.Interest, InterestAdmin)


class ActionAdmin(admin.ModelAdmin):
    list_display = ('order', 'name')
    prepopulated_fields = {"name_slug": ("name", )}
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
