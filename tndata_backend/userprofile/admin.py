from django.contrib import admin
from . import models

from utils.admin import UserRelatedModelAdmin


class UserProfileAdmin(UserRelatedModelAdmin):
    list_display = (
        'user', 'user_email', 'user_first', 'user_last',
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
    )
admin.site.register(models.UserProfile, UserProfileAdmin)
