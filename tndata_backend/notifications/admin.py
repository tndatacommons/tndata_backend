from django.contrib import admin
from . import models


class GCMDeviceAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'device_name', 'is_active', 'created_on', 'updated_on',
    )
    list_filter = ('is_active', )
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name', 'user__email',
        'registration_id', 'device_name',
    ]
admin.site.register(models.GCMDevice, GCMDeviceAdmin)


class GCMMessageAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'message_id', 'deliver_on', 'success', 'response_code',
    )
    list_filter = ('success', 'response_code')
    search_fields = ['message_id', ]
    actions = ['send_notification']

    def send_notification(self, request, queryset):
        for obj in queryset:
            obj.send()
    send_notification.short_description = "Send Message via GCM"

admin.site.register(models.GCMMessage, GCMMessageAdmin)
