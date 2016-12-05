from datetime import datetime
from django import forms
from django.utils import timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, HTML, Layout


class ContactForm(forms.Form):
    your_name = forms.CharField(max_length=256)
    email = forms.EmailField()
    phone = forms.CharField(max_length=256)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # Don't generate <form> tags
        self.helper.template_pack = "mdl"

        self.helper.layout = Layout(
            Field('your_name', css_class="mdl-textfield__input"),
            Field('email', css_class="mdl-textfield__input"),
            Field('phone', css_class="mdl-textfield__input"),
        )
