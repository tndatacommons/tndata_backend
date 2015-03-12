from django.contrib import admin
from . import models


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'title_slug', 'order')
    prepopulated_fields = {"title_slug": ("title", )}

admin.site.register(models.Category, CategoryAdmin)


class GoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'title_slug', 'in_categories')
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


class BehaviorSequenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'in_categories', 'in_goals')
    prepopulated_fields = {"name_slug": ("name", )}

    def in_categories(self, obj):
        return ", ".join(sorted([cat.title for cat in obj.categories.all()]))

    def in_goals(self, obj):
        return ", ".join(sorted([g.title for g in obj.goals.all()]))
admin.site.register(models.BehaviorSequence, BehaviorSequenceAdmin)


class BehaviorActionAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'sequence', 'sequence_order')
    prepopulated_fields = {"name_slug": ("name", )}
admin.site.register(models.BehaviorAction, BehaviorActionAdmin)
