from django.contrib import admin
from .models import ChatGroup, ChatMessage


@admin.register(ChatGroup)
class ChatGroupAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'created_on', 'members_count', )
    search_fields = ('room', 'text', 'digest')
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ('user', 'members')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'text', 'read', 'created_on')
    search_fields = ('room', 'text', 'digest')
    list_filter = ('read', )
    raw_id_fields = ('user', )
