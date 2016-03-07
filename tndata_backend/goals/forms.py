import re

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import Q

from django.forms import ValidationError
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Div,
    Field,
    Fieldset,
    HTML,
    Layout,
)

from recurrence import serialize as serialize_recurrences
from recurrence.forms import RecurrenceField
from utils.db import get_max_order
from utils.user_utils import date_hash
from utils.widgets import TextareaWithMarkdownHelperWidget

from . models import Action, Behavior, Category, Goal, Trigger
from . permissions import ContentPermissions, is_content_editor
from . utils import read_uploaded_csv
from . widgets import TimeSelectWidget


class DisableTriggerForm(forms.Form):
    ok = forms.BooleanField(initial=True, widget=forms.HiddenInput)


class ActionForm(forms.ModelForm):
    """A Form for creating/updating actions. This form orders related behaviors
    alphabetically."""

    # Initial content for differnt types of Actions
    INITIAL = {
        Action.TINY: {
            'title': 'Try a tiny version',
            'notification_text': 'Try a tiny version',
            'description': "",
            'more_info': (
                "Large tasks can seem intimidating and difficult. Instead of "
                "trying to tackle them all at once, try starting with a "
                "“tiny action.”\n"
                "A tiny action is simply a tinier version of your target task. "
                "Tiny versions will make you feel successful and motivated to "
                "take on your larger goal. So try whittling your goal down to "
                "its smallest parts, and start celebrating tiny victories on "
                "your path to achievement!"
            ),
            'action_type': Action.TINY,
        },
        Action.STARTER: {
            'title': 'Try a starter step',
            'notification_text': 'Try a starter step',
            'description': "",
            'more_info': (
                "Sometimes we let the little things prevent us from starting "
                "the tasks we want to do. Make activities more manageable by "
                "taking a “starter step.”\n"
                "A starter step is the first small action in a sequence of "
                "actions that lead to your ultimate goal. When you perform "
                "these small steps, you make your task more manageable and "
                "prepare yourself for success."
            ),
            'action_type': Action.STARTER,
        },
        Action.RESOURCE: {
            'title': 'Try a helpful tool',
            'notification_text': 'Try a helpful tool',
            'description': "",
            'more_info': (
                "We’ve picked some of the best tools and resources to help "
                "you succeed. Give them a try."
            ),
            'action_type': Action.RESOURCE,
        },
        Action.NOW: {
            'title': 'Do it now',
            'notification_text': 'Do it now',
            'description': "",
            'more_info': (
                "When it comes to achieving your goals, there’s no time like "
                "the present. Consider performing this action right now, while "
                "it’s fresh on your mind."
            ),
            'action_type': Action.NOW,
        },
        Action.LATER: {
            'title': 'Do it later',
            'notification_text': 'Do it later',
            'description': "",
            'more_info': (
                "Life is demanding. If you can’t do this right now, don’t "
                "worry! Set a reminder to do it later."
            ),
            'action_type': Action.LATER,
        },
        Action.CUSTOM: {
            'action_type': Action.CUSTOM,
        },
    }

    behavior = forms.ModelChoiceField(
        queryset=Behavior.objects.all().order_by("title")
    )

    # Note: this field's value should always get in the initial data
    action_type = forms.CharField(
        max_length=32,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Action
        fields = [
            'notification_text', 'sequence_order', 'behavior', 'title',
            'description', 'more_info', 'external_resource',
            'external_resource_name', 'source_link', 'source_notes',
            'notes', 'icon', 'action_type', 'priority',
        ]
        labels = {"notes": "Scratchpad"}
        widgets = {
            "description": TextareaWithMarkdownHelperWidget(),
            "more_info": TextareaWithMarkdownHelperWidget(),
        }

    class Media:
        js = (
            "foundation/js/vendor/jquery.js",
            "js/action_form.js",
        )

    def _get_priority_options(self):
        if self.user is None:
            return Action.PRIORITY_CHOICES[0:1]  # Only LOW
        elif is_content_editor(self.user):
            return Action.PRIORITY_CHOICES  # All priorities.
        else:
            return Action.PRIORITY_CHOICES[0:2]  # LOW - MEDIUM

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        notify_label = Action._notification_text.replace(" {}", "")
        self.fields['notification_text'].label = notify_label

        # Restrict priority options based on the user's permissions.
        self.fields['priority'].choices = self._get_priority_options()

    def clean_priority(self):
        """Ensure we have a legit priority."""
        priority = self.cleaned_data['priority']
        valid_options = [t[0] for t in self._get_priority_options()]
        if priority not in valid_options:
            err = "%(value)s is not a valid priority"
            raise ValidationError(err, params={"value": priority})
        return priority


class BehaviorForm(forms.ModelForm):
    """A Form for creating/updating behaviors. This form orders related
    goals alphabetically."""
    goals = forms.ModelMultipleChoiceField(
        queryset=Goal.objects.all().order_by("title")
    )

    class Meta:
        model = Behavior
        fields = [
            'title', 'sequence_order', 'description', 'more_info',
            'informal_list', 'notes', 'external_resource',
            'external_resource_name', 'goals', 'icon',
            'source_link', 'source_notes',
        ]
        labels = {"notes": "Scratchpad", 'informal_list': 'Action List'}
        widgets = {
            "description": TextareaWithMarkdownHelperWidget(),
            "more_info": TextareaWithMarkdownHelperWidget(),
        }


def _authors():
    """Returns a QuerySet of Users that are Content Authors.

    Those users are either staff or have the ContentAuthor ContentPermissions
    (either permissions directory or through a Group membership).

    """
    User = get_user_model()
    return User.objects.filter(
        Q(user_permissions__codename__in=ContentPermissions.author_codenames) |
        Q(groups__permissions__codename__in=ContentPermissions.author_codenames) |
        Q(is_staff=True)
    ).distinct()


def _contributors():
    """Returns a QuerySet of Users that can be Package Contributors.

    Those users are either staff or have ContentPermissions (either permissions
    directory or through a Group membership).

    """
    User = get_user_model()
    return User.objects.filter(
        Q(user_permissions__codename__in=ContentPermissions.all_codenames) |
        Q(groups__permissions__codename__in=ContentPermissions.all_codenames) |
        Q(is_staff=True)
    ).distinct()


class ContributorChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
            return obj.get_full_name()


class AuthorChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
            return obj.get_full_name()


class ContentAuthorForm(forms.Form):
    """A form that lets us select a content author. This is used in the Transfer
    view, to move ownership from one author to another."""
    user = AuthorChoiceField(
        queryset=_authors(),
        help_text="Select the new owner for this item."
    )


class CategoryForm(forms.ModelForm):
    """A Form for creating/updateing Categories. This form customizes the widget
    for the color field."""

    package_contributors = ContributorChoiceField(
        queryset=_contributors(),
        required=False
    )

    class Meta:
        model = Category
        fields = [
            'packaged_content', 'package_contributors',
            'prevent_custom_triggers_default',
            'display_prevent_custom_triggers_option',
            'order', 'title', 'description', 'icon', 'image', 'color',
            'secondary_color', 'notes', 'consent_summary', 'consent_more',
        ]
        labels = {
            "order": "Default Order",
            "notes": "Scratchpad",
            'prevent_custom_triggers_default': 'Prevent custom triggers by default',
            'display_prevent_custom_triggers_option': (
                'Display trigger restriction option during enrollment'
            )
        }
        widgets = {
            "description": TextareaWithMarkdownHelperWidget(),
            "color": forms.TextInput(attrs={'class': 'color-picker', 'type': 'color'}),
            "secondary_color": forms.TextInput(attrs={'class': 'color-picker', 'type': 'color'}),
            "consent_summary": TextareaWithMarkdownHelperWidget(),
            "consent_more": TextareaWithMarkdownHelperWidget(),
        }

    def __init__(self, *args, **kwargs):
        # Set a default color / secondary color
        initial = kwargs.get('initial', {})
        instance = kwargs.get('instance')

        if not instance and initial.get('color') is None:
            initial['color'] = Category.DEFAULT_PRIMARY_COLOR
        if not instance and initial.get('secondary_color') is None:
            initial['secondary_color'] = Category.DEFAULT_SECONDARY_COLOR
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

        # Configure crispy forms.
        self.helper = FormHelper()
        self.helper.form_tag = False  # Don't generate <form> tags
        self.helper.layout = Layout(
            Div(
                Div(
                    Fieldset(
                        _("Category Details"),
                        'order',
                        'title',
                        'description',
                        'icon',
                        'image',
                        'color',
                        'secondary_color',
                    ),
                    css_class="large-6 small-12 columns"
                ),
                Div(
                    Fieldset(
                        _("Scratchpad"),
                        Div(
                            Field('notes'),
                            css_class="panel"
                        ),
                    ),
                    Fieldset(
                        _("Packaged Content"),
                        'packaged_content',
                        'package_contributors',
                        'prevent_custom_triggers_default',
                        'display_prevent_custom_triggers_option',
                        'consent_summary',
                        'consent_more',
                    ),
                    css_class="large-6 small-12 columns"
                ),
                css_class="row"
            )
        )


class GoalForm(forms.ModelForm):
    """A Form for creating/updating goals. This form orders related categories
    alphabetically."""
    categories = forms.ModelMultipleChoiceField(queryset=Category.objects.all().order_by("title"))

    class Meta:
        model = Goal
        fields = [
            'categories', 'keywords', 'title', 'description',
            'more_info', 'icon', 'notes',
        ]
        labels = {"notes": "Scratchpad"}
        widgets = {
            "description": TextareaWithMarkdownHelperWidget(),
            "more_info": TextareaWithMarkdownHelperWidget(),
        }


class ActionTriggerForm(forms.ModelForm):
    """A form for creating a default trigger while creating an action."""
    recurrences = RecurrenceField(
        help_text="Select the rules to define how this reminder should repeat."
    )

    class Meta:
        model = Trigger
        fields = [
            'time_of_day', 'frequency', 'start_when_selected',
            'stop_on_complete', 'time', 'trigger_date',
            'relative_value', 'relative_units', 'recurrences',
        ]
        widgets = {
            "time": TimeSelectWidget(include_empty=True),
            "trigger_date": forms.TextInput(attrs={'class': 'datepicker'}),
        }
        labels = {
            "time": "Reminder Time",
            "trigger_date": "Reminder Date",
        }

    class Media:
        js = (
            "foundation/js/vendor/jquery.js",
            "js/action_trigger_form.js",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If there's a trigger instance, include a button to disable it. This
        # should be handled in the template.
        try:
            if self.instance.action_default:
                disable_button = HTML(
                    '<button type="button" id="disable-trigger-button" '
                    ' class="button info tiny pull-right">'
                    '<i class="fa fa-bell-slash"></i> Remove Trigger</button><hr/>'
                )
        except ObjectDoesNotExist:
            disable_button = HTML('')

        self.fields['time'].help_text = (
            "Set the time at which the notification should be sent"
        )
        self.fields['trigger_date'].help_text = (
            "The date on which notifications should start"
        )

        # Better label names for the Relative Reminders
        self.fields['relative_value'].label = 'Relative Reminder'
        self.fields['relative_units'].label = '&nbsp;'

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                _("Reminder Details"),
                disable_button,
                'time_of_day',
                'frequency',
                # NOTE: advanced options are hidden by default and may
                #       override the above dynamic/automatic notifications.
                # -------------------------------------------------------------
                HTML('<hr/><strong>Advanced Options</strong>'),
                HTML('<a class="button tiny secondary right" id="advanced" '
                     'data-status="hidden"><i class="fa fa-chevron-right"></i>'
                     ' Show</a>'),
                Div(
                    HTML("<hr/><p class='alert-box warning'>"
                         "<i class='fa fa-warning'></i> These options may "
                         "override any options set above</p>"),
                    Div(
                        Div('time', css_class="large-6 columns"),
                        Div('trigger_date', css_class="large-6 columns"),
                    ),
                    Div(
                        Field(
                            'stop_on_complete',
                            data_tooltip=None,
                            aria_haspopup="true",
                            title=("Reminders will cease to fire once the user "
                                   "has completed this action."),
                            css_class="has-tip tip-top"
                        ),
                    ),
                    Field(
                        'start_when_selected',
                        data_tooltip=None,
                        aria_haspopup="true",
                        title=("If selected the reminder date will be automatically "
                               "be set when the user adds this action."),
                        css_class="has-tip tip-top"
                    ),
                    Div(
                        Div('relative_value', css_class="large-6 columns"),
                        Div('relative_units', css_class="large-6 columns"),
                        css_class="row"
                    ),
                    Div(
                        Div(
                            HTML('<div class="hint">Relative reminders will fire '
                                 'based on when the user adopts an action. Select '
                                 'the amount time after the user adds the action '
                                 'that this reminder should start</div>'),
                            css_class="large-12 columns"
                        ),
                        css_class="row"
                    ),
                    'recurrences',
                    css_class="trigger-form-advanced"
                )
            )
        )

    def save(self, *args, **kwargs):
        obj = super().save(*args, **kwargs)
        obj.name = date_hash()
        return obj

    def clean(self):
        data = super().clean()
        recurrences = data.get('recurrences')
        date = data.get('trigger_date')
        rel_value = data.get('relative_value')
        rel_units = data.get('relative_units')
        start_when_selected = data.get('start_when_selected', False)

        # Require BOTH relative_value and relative_units
        if (rel_value or rel_units) and not all([rel_value, rel_units]):
            self.add_error('relative_value', ValidationError(
                "Both a value and units are required for Relative Reminders",
                code="required_for_relative_reminders"
            ))

        if not start_when_selected and not date:
            # Intervals (e.g. every other day) need a starting date.
            if recurrences and 'INTERVAL' in serialize_recurrences(recurrences):
                self.add_error('trigger_date', ValidationError(
                    "A Trigger Date is required for recurrences that contain an "
                    "interval (such as every 2 days)", code="required_for_intervals"
                ))
            elif recurrences and 'COUNT' in serialize_recurrences(recurrences):
                self.add_error('trigger_date', ValidationError(
                    "A Trigger Date is required for recurrences that occur a set "
                    "number of times", code="required_for_count"
                ))
        return data


class TriggerForm(forms.ModelForm):
    recurrences = RecurrenceField(
        help_text="Select the rules to define how this reminder should repeat."
    )

    class Meta:
        model = Trigger
        fields = ['name', 'time', 'trigger_date', 'recurrences']
        widgets = {
            "time": TimeSelectWidget(),
            "trigger_date": forms.TextInput(attrs={'class': 'datepicker'}),
        }
        labels = {
            "time": "Reminder Time",
            "trigger_date": "Reminder Date",
        }

    def clean(self):
        data = super().clean()
        recurrences = data.get('recurrences')
        date = data.get('trigger_date')

        # Intervals (e.g. every other day) need a starting date.
        if recurrences and 'INTERVAL' in serialize_recurrences(recurrences) and not date:
            self.add_error('trigger_date', ValidationError(
                "A Trigger Date is required for recurrences that contain an "
                "interval (such as every 2 days)", code="required_for_intervals"
            ))
        elif recurrences and 'COUNT' in serialize_recurrences(recurrences) and not date:
            self.add_error('trigger_date', ValidationError(
                "A Trigger Date is required for recurrences that occur a set "
                "number of times", code="required_for_count"
            ))

        return data


class PackageEnrollmentForm(forms.Form):
    """Allows input of email addresses (in a text box) and the selection of
    one or more Categories--those of which have been designated as packaged
    content.

    Requires that it's first argument is a Category, the parent (or package)
    of the goals to be selected.

    """
    email_addresses = forms.CharField(
        widget=forms.Textarea(),
        help_text=("Paste in email addresses for people who should be enrolled, "
                   "either one per line or separated by a comma")
    )
    packaged_goals = forms.ModelMultipleChoiceField(
        queryset=Goal.objects.packages(),
        help_text="Select the packages in which to enroll each person"
    )
    prevent_custom_triggers = forms.BooleanField(
        label="Prevent custom reminders",
        required=False,
        help_text=(
            "Setting this option will prevent users from overriding the "
            "default reminder times for actions within the selected goals."
        )
    )

    def __init__(self, category, *args, **kwargs):
        """Provice a specific category for this for in order to enroll users
        in it's set of Goals."""

        # set the initial value for this field if it's defined on the category
        if category.prevent_custom_triggers_default:
            kwargs['initial'] = {'prevent_custom_triggers': True}

        super().__init__(*args, **kwargs)
        qs = Goal.objects.packages(categories=category)
        self.fields['packaged_goals'].queryset = qs

        # See whether or not we want to hide this field.
        if not category.display_prevent_custom_triggers_option:
            self.fields['prevent_custom_triggers'].widget = forms.HiddenInput()

    def clean_email_addresses(self):
        """Returns a list of email addresses."""
        content = self.cleaned_data['email_addresses']
        emails = [email for email in re.split(r"\s|,", content) if email.strip()]
        for email in emails:
            try:
                validate_email(email)
            except ValidationError:
                raise ValidationError(
                    "%(value)s is not a valid email address.",
                    params={'value': email}
                )
        return emails


class AcceptEnrollmentForm(forms.Form):
    """forces the user to accept some terms."""
    i_accept = forms.BooleanField(
        required=True,
        help_text="I wish to participate"
    )
    age_restriction = forms.BooleanField(
        required=True,
        help_text="I am at least 14 years old."
    )
    accept_terms = forms.BooleanField(
        required=True,
        help_text=(
            'I accept the Data Commons/Compass '
            '<a href="/terms/" target="_blank">Terms of Service</a> '
            'and <a href="/privacy/">Privacy Notice</a>.'
        )
    )

    def __init__(self, *args, **kwargs):
        package = kwargs.pop("package", None)
        if package and package.accepted:
            kwargs['initial'] = {
                'i_accept': True,
                'age_restriction': True,
                'accept_terms': True
            }
        super().__init__(*args, **kwargs)


class CTAEmailForm(forms.Form):
    """This form is used to create an arbitrary Email for users in a Package.
    It may contain a CTA link (and text) as well as a subject and message for
    the user.

    """
    subject = forms.CharField(
        help_text="The subject of your email.",
        required=True,
    )
    message = forms.CharField(
        widget=forms.Textarea,
        required=True,
        help_text="This is the body of your email message."
    )
    link = forms.URLField(
        required=False,
        help_text="(Optional) A link that you want users to click on."
    )
    link_text = forms.CharField(
        required=False,
        help_text="(Optional) The Call-To-Action text for the above link."
    )


class EnrollmentReminderForm(forms.Form):
    """This form is used to create a Reminder email for enrollees that have
    not yet accepted the package enrollment. It's content get automatically
    pre-populated with some email content.

    """
    message = forms.CharField(
        widget=forms.Textarea,
        help_text="The message that you type above will replace the original "
                  "content in the first enrollment email, but it will still "
                  "contain the link for the user to accept the enrollment."
    )

    def _initial_message(self):
        return (
            "We haven't heard from you yet, but we wanted to let you know "
            "there's still time to get started! "
        )

    def __init__(self, *args, **kwargs):
        if 'initial' not in kwargs:
            kwargs['initial'] = {'message': self._initial_message()}
        super().__init__(*args, **kwargs)


class InvalidFormatException(Exception):
    """Custom exception that gets raised when the CSVUploadForm fails."""
    pass


class CSVUploadForm(forms.Form):
    InvalidFormat = InvalidFormatException
    VALID_TYPES = ['action', 'category']

    csv_file = forms.FileField(
        help_text="Upload a CSV file to populate the content library"
    )

    def _read_file(self):
        uploaded_file = self.cleaned_data['csv_file']
        if uploaded_file.content_type != 'text/csv':
            raise self.InvalidFormat(
                "{0} is not a CSV File".format(uploaded_file.content_type)
            )
        content = read_uploaded_csv(uploaded_file)
        return content

    def _get_type(self, row):
        try:
            row_type = row[0].lower().strip().replace(' ', '')
        except(IndexError, ValueError):
            row_type = None
        if row_type not in self.VALID_TYPES:
            raise self.InvalidFormat("File contains invalid data types")
        return row_type

    def _create_category(self, row):
        title = row[1]
        desc = row[2]
        try:
            # Update the description if this exists.
            category = Category.objects.get(title_slug=slugify(title))
            category.description = desc
            category.save()
        except Category.DoesNotExist:
            order = get_max_order(Category)
            Category.objects.create(order=order, title=title, description=desc)

    def process_row(self, row):
        # A mapping between the row type and the method that should process it
        method_map = {
            'action': self._create_action,
            'category': self._create_category,
        }
        row_type = self._get_type(row)
        method_map[row_type](row)

    def save(self):
        """Once the form's `is_valid` method has been called, this method
        can read and parse the content from the uploaded file, then using the
        input data to create new models.

        """
        try:
            with transaction.atomic():
                for row in self._read_file():
                    self.process_row(row)
        except (ObjectDoesNotExist, IntegrityError) as e:
            raise self.InvalidFormat(
                "There was a problem saving your data: {0}".format(e)
            )


class UploadImageForm(forms.Form):
    """A Simple file upload form. This accepts 1 parameter named 'file', and
    validates that it's an image. This is used in the async upload handler.

    See views.file_upload

    """
    file = forms.ImageField()


class TitlePrefixForm(forms.Form):
    prefix = forms.CharField(
        help_text="Prefix text for all new Titles",
        required=True,
    )
