from django.contrib import admin
from django.utils import timezone

from . import models


class GCMDeviceAdmin(admin.ModelAdmin):
    list_display = (
        'user_email', 'user_username', 'regid', 'device_name', 'is_active',
        'created_on',
    )
    list_filter = ('is_active', )
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name', 'user__email',
        'registration_id', 'device_name',
    ]

    def user_username(self, obj):
        return obj.user.username

    def user_email(self, obj):
        return obj.user.email

    def regid(self, obj):
        """registration id, teaser."""
        return ''.join([obj.registration_id[:20], "..."])

admin.site.register(models.GCMDevice, GCMDeviceAdmin)


class GCMMessageAdmin(admin.ModelAdmin):
    list_display = (
        'user_email', 'user_username', 'message_id', 'title',
        'deliver_on', 'expire_on', 'success', 'response_code',
    )
    list_filter = ('success', 'response_code')
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name', 'user__email',
        'message_id', 'title', 'message'
    ]
    actions = ['send_notification', 'expire_messages']

    def user_username(self, obj):
        return obj.user.username

    def user_email(self, obj):
        return obj.user.email

    def send_notification(self, request, queryset):
        for obj in queryset:
            obj.send()
    send_notification.short_description = "Send Message via GCM"

    def expire_messages(self, request, queryset):
        queryset = queryset.filter(expire_on__lte=timezone.now())
        queryset.delete()
    expire_messages.short_description = "Remove Expired Messages"

admin.site.register(models.GCMMessage, GCMMessageAdmin)
