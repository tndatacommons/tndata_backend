from django.contrib import admin
from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'text', 'read', 'created_on')
    raw_id_fields = ('user', )
