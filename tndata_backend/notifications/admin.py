from django.contrib import admin
from . import models


class GCMMessageAdmin(admin.ModelAdmin):
    list_display = (
        'message_id', 'registration_id', 'deliver_on', 'success', 'response_code',
    )
    list_filter = ('success', 'response_code')
    search_fields = ['message_id', 'registration_id']

admin.site.register(models.GCMMessage, GCMMessageAdmin)
