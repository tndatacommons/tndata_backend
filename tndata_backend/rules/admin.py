from django.contrib import admin
from . import models


class RuleAdmin(admin.ModelAdmin):
    list_display = ('app_name', 'created', 'modified')
admin.site.register(models.Rule, RuleAdmin)
