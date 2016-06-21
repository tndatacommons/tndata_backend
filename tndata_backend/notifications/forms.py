from django import forms
from . models import GCMMessage


class GCMMessageForm(forms.ModelForm):
    class Meta:
        model = GCMMessage
        fields = ['title', 'message', 'content_type', 'object_id']
