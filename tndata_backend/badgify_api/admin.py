from django.contrib import admin
from badgify.models import Award
from badgify.admin import AwardAdmin


class CustomAwardAdmin(AwardAdmin):
    """Override the default AwardAdmin class."""
    list_display = ('user_fullname', 'user_email', 'badge', 'awarded_at')
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'badge__name', 'badge__description',
    )

    def user_fullname(self, award):
        return award.user.get_full_name()
    user_fullname.admin_order_field = 'user'

    def user_email(self, award):
        return award.user.email
    user_email.admin_order_field = 'user'


admin.site.unregister(Award)
admin.site.register(Award, CustomAwardAdmin)
