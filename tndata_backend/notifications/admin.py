from django.contrib import admin
from django.template.defaultfilters import mark_safe
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
    readonly_fields = ('device_name', 'registration_id')

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
        'user_email', 'user_username', 'title', 'message_teaser',
        'deliver_on', 'success', 'created_on',
    )
    list_filter = ('success', 'response_code')
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name', 'user__email',
        'message_id', 'title', 'message'
    ]
    exclude = ('response_text', )
    readonly_fields = (
        'message_id', 'success', 'response_code', 'gcm_response', 'expire_on',
        'registration_ids', 'created_on',
    )
    actions = ['send_notification', 'expire_messages']

    def registration_ids(self, obj):
        """List all the registration IDs for the message's user."""
        if obj.user:
            ids = obj.user.gcmdevice_set.values_list("registration_id", flat=True)
            ids = "\n".join(ids)
            return mark_safe("<pre>{0}</pre>".format(ids))
        return ''
    registration_ids.short_description = "Registration IDs"
    registration_ids.allow_tags = True

    def gcm_response(self, obj):
        """Formatting for the response_text that GCM sets."""
        return mark_safe("<pre>{0}</pre>".format(obj.response_text))
    gcm_response.short_description = "GCM Response"
    gcm_response.allow_tags = True

    def message_teaser(self, obj):
        return "{0}...".format(obj.message[:32])

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
