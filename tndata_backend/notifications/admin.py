from datetime import timedelta
from pprint import pformat

from django.contrib import admin
from django.template.defaultfilters import mark_safe
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from . import models


class GCMDeviceAdmin(admin.ModelAdmin):
    list_display = (
        'user_email', 'user_username', 'device_name', 'device_id', 'regid',
        'device_type', 'updated_on',
    )
    list_filter = ('device_type', )
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name', 'user__email',
        'device_name', 'device_id', 'registration_id', 'device_name',
    ]
    readonly_fields = ('device_name', 'device_id', 'registration_id')
    raw_id_fields = ('user', )

    def user_username(self, obj):
        return obj.user.username

    def user_email(self, obj):
        return obj.user.email

    def regid(self, obj):
        """registration id, teaser."""
        return ''.join([obj.registration_id[:20], "..."])

admin.site.register(models.GCMDevice, GCMDeviceAdmin)


class DeliverDayListFilter(admin.SimpleListFilter):
    title = _('Delivery Day')
    parameter_name = 'deliver'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        dt = timezone.now()
        today = dt.strftime("%Y-%m-%d")
        tomorrow = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday = (dt - timedelta(days=1)).strftime("%Y-%m-%d")

        return (
            (today, _('Today')),
            (tomorrow, _('Tomorrow')),
            (yesterday, _('Yesterday')),
        )

    def queryset(self, request, queryset):
        day = self.value()
        if day:
            queryset = queryset.filter(deliver_on__startswith=day)
        return queryset


class GCMMessageAdmin(admin.ModelAdmin):
    date_hierarchy = 'deliver_on'
    list_display = (
        'user_email', 'user_username', 'title', 'message_teaser',
        'content_type', 'object_id', 'deliver_on', 'success', 'response_text',
        'queue_id',
    )
    list_filter = (DeliverDayListFilter, 'success', 'content_type')
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name', 'user__email',
        'title', 'message', 'content_type__model', 'queue_id', 'object_id',
    ]
    exclude = ('response_text', 'registration_ids', 'response_data')
    readonly_fields = (
        'pretty_payload',
        'success', 'response_text', 'response_code', 'gcm_response',
        'pretty_response_data', 'delivered_to', 'registered_devices',
        'gcm_diagnostics', 'created_on', 'expire_on', 'queue_id',
    )
    actions = ['send_notification', 'expire_messages']
    raw_id_fields = ('user', )

    def pretty_payload(self, obj):
        """pretty-printed version of the `content_json` attribute delivered as
        a payload to GCM."""
        return mark_safe("<br/><pre>{0}</pre>".format(pformat(obj.content)))
    pretty_payload.short_description = "GCM Payload"
    pretty_payload.allow_tags = True

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
        return mark_safe("<br/><pre>{0}</pre>".format(data))
    pretty_response_data.short_description = "GCM Response Data"
    pretty_response_data.allow_tags = True

    def delivered_to(self, obj):
        """This is the list of registration_ids that we get back from GCM
        after sending the message"""
        return mark_safe("<br/><pre>{0}</pre>".format(obj.registration_ids))
    delivered_to.short_description = "Delivered to"
    delivered_to.allow_tags = True

    def registered_devices(self, obj):
        """List all the registration IDs owned by the user."""
        if obj.user:
            ids = "\n".join(obj.registered_devices)
            return mark_safe("<br/><pre>{0}</pre>".format(ids))
        return ''
    registered_devices.short_description = "Registered Devices"
    registered_devices.allow_tags = True

    def gcm_response(self, obj):
        """Formatting for the response_text that GCM sets."""
        return mark_safe("<br/><pre>{0}</pre>".format(obj.response_text))
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
