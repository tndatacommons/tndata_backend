from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms_foundation.layout.fields import Field


class ContactForm(forms.Form):
    your_name = forms.CharField(max_length=256)
    email = forms.EmailField()
    phone = forms.CharField(max_length=256)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # Don't generate <form> tags

        self.helper.layout = Layout(
            Field('your_name'),
            Field('email'),
            Field('phone'),
        )
