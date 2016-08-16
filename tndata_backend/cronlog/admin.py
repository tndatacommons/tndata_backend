from django.contrib import admin
from . models import CronLog


class CronLogAdmin(admin.ModelAdmin):
    list_display = ('command', 'message', 'host', 'created_on')
    list_filter = ('command', 'host', )
    search_fields = ['command', 'message', 'host']
    readonly_fields = ('command', 'message', 'host', 'created_on')

admin.site.register(CronLog, CronLogAdmin)
