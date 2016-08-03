from django.contrib import admin
from . models import CronLog


class CronLogAdmin(admin.ModelAdmin):
    list_display = ('command', 'message', 'created_on')
    list_filter = ('command', )
    search_fields = ['command', 'message']
    readonly_fields = ('command', 'message', 'created_on')

admin.site.register(CronLog, CronLogAdmin)
