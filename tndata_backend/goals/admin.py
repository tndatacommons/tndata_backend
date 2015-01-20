from django.contrib import admin
from . import models


class InterestGroupInline(admin.TabularInline):
    model = models.InterestGroup
    fields = ('category', 'interests', 'name', 'public')


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'name', 'name_slug', 'contains_groups')
    prepopulated_fields = {"name_slug": ("name", )}
    inlines = [InterestGroupInline]

    def contains_groups(self, obj):
        return ", ".join([g.name for g in obj.groups])
admin.site.register(models.Category, CategoryAdmin)


class InterestGroupInlineForInterestAdmin(admin.TabularInline):
    """This inline allows selection of InterestGroups while editing an Interest."""
    model = models.InterestGroup.interests.through


class InterestAdmin(admin.ModelAdmin):
    list_display = ('order', 'name', 'found_in_categories', 'found_in_groups')
    list_display_links = ('order', 'name')
    prepopulated_fields = {"name_slug": ("name", )}
    inlines = [InterestGroupInlineForInterestAdmin]

    def found_in_categories(self, obj):
        return ", ".join([c.name for c in obj.categories])

    def found_in_groups(self, obj):
        return ", ".join([g.name for g in obj.groups])
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
