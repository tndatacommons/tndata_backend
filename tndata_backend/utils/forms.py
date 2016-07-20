from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout


class EmailForm(forms.Form):
    """A simple form that validates a single email address."""
    email_address = forms.EmailField()


class SetNewPasswordForm(forms.Form):
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput,
        help_text="Enter a password that is 8 characters or longer"
    )
    password_confirmation = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput,
        help_text="Confirm your new password"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # Don't generate <form> tags
        self.helper.layout = Layout(
            Div(
                Div(
                    'password',
                    css_class="large-6 small-12 columns"
                ),
                Div(
                    'password_confirmation',
                    css_class="large-6 small-12 columns"
                ),
                css_class="row"
            )
        )

    def clean(self):
        """Ensure passwords match."""
        d = super(SetNewPasswordForm, self).clean()
        if d.get('password', 1) != d.get('password_confirmation', 2):
            raise forms.ValidationError("Your passwords do not match.")
        return d
