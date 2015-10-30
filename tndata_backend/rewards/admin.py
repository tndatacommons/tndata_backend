from django.contrib import admin
from .models import FunContent


class FunContentAdmin(admin.ModelAdmin):
    list_display = ('message_type', 'message', 'author')
    search_fields = ['message', 'author', ]
    list_filter = ('message_type', 'author',)

admin.site.register(FunContent, FunContentAdmin)
