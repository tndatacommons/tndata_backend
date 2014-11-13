from django.contrib import admin
from . import models


class MultipleChoiceResponseOptionInline(admin.TabularInline):
    model = models.MultipleChoiceResponseOption


class MultipleChoiceQuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'order', 'available')
    inlines = [
        MultipleChoiceResponseOptionInline,
    ]
admin.site.register(models.MultipleChoiceQuestion, MultipleChoiceQuestionAdmin)


class MultipleChoiceResponseAdmin(admin.ModelAdmin):
    list_display = ('question', 'selected_option', 'submitted_on')
admin.site.register(models.MultipleChoiceResponse, MultipleChoiceResponseAdmin)


class OpenEndedQuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'order', 'available')
admin.site.register(models.OpenEndedQuestion, OpenEndedQuestionAdmin)


class OpenEndedResponseAdmin(admin.ModelAdmin):
    list_display = ('question', 'response', 'submitted_on')
admin.site.register(models.OpenEndedResponse, OpenEndedResponseAdmin)


class GoalAdmin(admin.ModelAdmin):
    list_display = ('category', 'text', 'order')
admin.site.register(models.Goal, GoalAdmin)


class LikertQuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'order', 'available')
admin.site.register(models.LikertQuestion, LikertQuestionAdmin)


class LikertResponseAdmin(admin.ModelAdmin):
    list_display = ('question', 'selected_option', 'submitted_on')
admin.site.register(models.LikertResponse, LikertResponseAdmin)
