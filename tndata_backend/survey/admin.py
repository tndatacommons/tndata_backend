from django.contrib import admin
from . import models

from utils.admin import UserRelatedModelAdmin


class InstrumentAdmin(admin.ModelAdmin):
    list_display = ("id", "title")
    search_fields = ['title', 'description']
admin.site.register(models.Instrument, InstrumentAdmin)


class MultipleChoiceResponseOptionInline(admin.TabularInline):
    model = models.MultipleChoiceResponseOption


class MultipleChoiceQuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'order', 'available')
    list_filter = ('instruments', )
    inlines = [
        MultipleChoiceResponseOptionInline,
    ]
admin.site.register(models.MultipleChoiceQuestion, MultipleChoiceQuestionAdmin)


class MultipleChoiceResponseAdmin(UserRelatedModelAdmin):
    list_display = (
        'user', 'user_email', 'user_first', 'user_last',
        'question', 'selected_option', 'submitted_on',
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
    )
admin.site.register(models.MultipleChoiceResponse, MultipleChoiceResponseAdmin)


class OpenEndedQuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'order', 'available')
    list_filter = ('instruments', )
admin.site.register(models.OpenEndedQuestion, OpenEndedQuestionAdmin)


class OpenEndedResponseAdmin(UserRelatedModelAdmin):
    list_display = (
        'user', 'user_email', 'user_first', 'user_last',
        'question', 'response', 'submitted_on',
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
    )
admin.site.register(models.OpenEndedResponse, OpenEndedResponseAdmin)


class LikertQuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'order', 'available')
    list_filter = ('instruments', )
admin.site.register(models.LikertQuestion, LikertQuestionAdmin)


class LikertResponseAdmin(UserRelatedModelAdmin):
    list_display = (
        'user', 'user_email', 'user_first', 'user_last',
        'question', 'selected_option', 'submitted_on',
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
    )
admin.site.register(models.LikertResponse, LikertResponseAdmin)


class BinaryQuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'order', 'available')
    list_filter = ('instruments', )
admin.site.register(models.BinaryQuestion, BinaryQuestionAdmin)


class BinaryResponseAdmin(UserRelatedModelAdmin):
    list_display = (
        'user', 'user_email', 'user_first', 'user_last',
        'question', 'selected_option', 'submitted_on',
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
    )
admin.site.register(models.BinaryResponse, BinaryResponseAdmin)


class SurveyResultAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "instrument", "score", "labels", "created_on")
    search_fields = (
        'instrument__title', 'labels',
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
    )
admin.site.register(models.SurveyResult, SurveyResultAdmin)
