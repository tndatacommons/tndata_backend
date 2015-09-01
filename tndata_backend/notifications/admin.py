from pprint import pformat

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
        'title', 'message'
    ]
    exclude = ('response_text', 'registration_ids', 'response_data')
    readonly_fields = (
        'success', 'response_code', 'gcm_response',
        'pretty_response_data', 'delivered_to', 'registered_devices',
        'gcm_diagnostics', 'created_on', 'expire_on',
    )
    actions = ['send_notification', 'expire_messages']

    def gcm_diagnostics(self, obj):
        """Print links to the GCM Diagnostics page."""
        output = "<p>n/a</p>"
        if obj.response_data and len(obj.response_data) > 0:
            output = "<ul>{0}</ul>"
            items = []
            for resp in obj.response_data:
                for d in resp.get('results', []):
                    message_id = d.get('message_id', None)
                    if message_id:
                        items.append('<li>{0}</li>'.format(message_id))
            if len(items) > 0:
                output = output.format("\n".join(items))
        return mark_safe(output)
    gcm_diagnostics.short_description = "GCM Message IDs"
    gcm_diagnostics.allow_tags = True

    def pretty_response_data(self, obj):
        """pretty-printed response data"""
        data = pformat(obj.response_data)
        return mark_safe("<pre>{0}</pre>".format(data))
    pretty_response_data.short_description = "GCM Response Data"
    pretty_response_data.allow_tags = True

    def delivered_to(self, obj):
        """This is the list of registration_ids that we get back from GCM
        after sending the message"""
        return mark_safe("<pre>{0}</pre>".format(obj.registration_ids))
    delivered_to.short_description = "Delivered to"
    delivered_to.allow_tags = True

    def registered_devices(self, obj):
        """List all the registration IDs owned by the user."""
        if obj.user:
            ids = "\n".join(obj.registered_devices)
            return mark_safe("<pre>{0}</pre>".format(ids))
        return ''
    registered_devices.short_description = "Registered Devices"
    registered_devices.allow_tags = True

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
