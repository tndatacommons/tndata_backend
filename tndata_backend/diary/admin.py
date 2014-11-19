from django.contrib import admin
from . import models


class FeelingAdmin(admin.ModelAdmin):
    list_display = ('rank', 'submitted_on')


admin.site.register(models.Feeling, FeelingAdmin)
