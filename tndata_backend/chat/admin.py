from django.contrib import admin
from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'room', 'read', 'created_on')
    raw_id_fields = ('from_user', 'to_user')
