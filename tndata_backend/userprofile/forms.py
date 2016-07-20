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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
