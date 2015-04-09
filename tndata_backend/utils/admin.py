from django.contrib import admin


class UserRelatedModelAdmin(admin.ModelAdmin):
    """This class contains methods that allow you to list user details in the
    list_display field. Use with objects that have a `user` related field."""

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Email"

    def user_first(self, obj):
        return obj.user.first_name
    user_first.short_description = "First Name"

    def user_last(self, obj):
        return obj.user.last_name
    user_last.short_description = "Last Name"
