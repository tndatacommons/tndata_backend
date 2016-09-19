from django import forms
from django.contrib.auth import get_user_model

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout

from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("timezone",  'maximum_daily_notifications')


class UserForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'email')

    def clean_first_name(self):
        value = self.cleaned_data['first_name']
        if len(value.strip()) == 0:
            raise forms.ValidationError("This field is required")
        return value

    def clean_last_name(self):
        value = self.cleaned_data['last_name']
        if len(value.strip()) == 0:
            raise forms.ValidationError("This field is required")
        return value

    def clean_email(self):
        value = self.cleaned_data['email']
        if len(value.strip()) == 0:
            raise forms.ValidationError("This field is required")
        return value

    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop('for_organization', None)
        super().__init__(*args, **kwargs)
        if self._organization:
            help = "Use the email you use with {}.".format(self._organization)
            self.fields['email'].help_text = help
        self.helper = FormHelper()
        self.helper.form_tag = False  # Don't generate <form> tags
        self.helper.layout = Layout(
            Div(
                Div(
                    'email',
                    css_class="large-12 small-12 columns"
                ),
                css_class="row"
            ),
            Div(
                Div(
                    'first_name',
                    css_class="large-6 small-12 columns"
                ),
                Div(
                    'last_name',
                    css_class="large-6 small-12 columns"
                ),
                css_class="row"
            )
        )
