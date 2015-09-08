from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from . import models

from utils.admin import UserRelatedModelAdmin


def remove_app_data(modeladmin, request, queryset):
    """Remove a user's selected content from the mobile app. This essentiall
    deletes their: UserAction, UserBehavior, UserCategory, BehaviorProgress,
    GoalProgress, CategoryProgress, PackageEnrollment, Trigger,
    UserCompletedAction instances as well as their GCMMessages.

    """
    for obj in queryset:
        if isinstance(obj, models.UserProfile):
            obj = obj.user

        obj.useraction_set.all().delete()
        obj.userbehavior_set.all().delete()
        obj.usergoal_set.all().delete()
        obj.usercategory_set.all().delete()
        obj.trigger_set.all().delete()
        obj.behaviorprogress_set.all().delete()
        obj.goalprogress_set.all().delete()
        obj.categoryprogress_set.all().delete()
        obj.usercompletedaction_set.all().delete()
        obj.packageenrollment_set.all().delete()
        obj.gcmmessage_set.all().delete()
remove_app_data.short_description = "Remove App Data"


class PlaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'updated_on', 'created_on')
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ('name',)
admin.site.register(models.Place, PlaceAdmin)


class UserPlaceAdmin(UserRelatedModelAdmin):
    list_display = ('user', 'user_email', 'user_first', 'user_last', 'place')
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'place__name',
    )
admin.site.register(models.UserPlace, UserPlaceAdmin)


class UserProfileAdmin(UserRelatedModelAdmin):
    list_display = (
        'user', 'user_email', 'user_first', 'user_last', 'timezone',
        'needs_onboarding'
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
    )
    actions = [remove_app_data]
admin.site.register(models.UserProfile, UserProfileAdmin)


class CustomUserAdmin(UserAdmin):
    """Override the default UserAdmin class so we can attach a custom action."""
    actions = [remove_app_data]
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
