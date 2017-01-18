from django.contrib import admin

from . import models


@admin.register(models.OfficeHours)
class OfficeHoursAdmin(admin.ModelAdmin):
    list_display = ('user', '__str__', 'expires_on', 'created_on')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user', )


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'full_name', 'name', 'start_time', 'location')
    list_filter = ('name', )
    search_fields = (
        'name', 'user__email', 'user__first_name', 'user__last_name', 'code'
    )
    raw_id_fields = ('user', 'students')

    def full_name(self, obj):
        return obj.user.get_full_name()
