from django.contrib import admin

from . import models


@admin.register(models.OfficeHours)
class OfficeHoursAdmin(admin.ModelAdmin):
    list_display = ('user', '__str__', 'expires_on', 'created_on')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'start_time', 'location')
    search_fields = ('name', 'user__email', 'user__first_name', 'user__last_name')
