from django.contrib import admin
from . import models


class EntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'rank', 'submitted_on')


admin.site.register(models.Entry, EntryAdmin)
