import re

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils.text import slugify

from recurrence.forms import RecurrenceField
from utils.db import get_max_order
from utils import colors
from utils.user_utils import date_hash

from . models import Action, Behavior, Category, Goal, Trigger
from . permissions import ContentPermissions
from . utils import read_uploaded_csv
from . widgets import TimeSelectWidget


class ActionForm(forms.ModelForm):
    """A Form for creating/updating actions. This form orders related behaviors
    alphabetically."""

    # Initial content for differnt types of Actions
    INITIAL = {
        Action.TINY: {
            'title': 'Try a tiny version',
            'notification_text': 'Try a tiny version',
            'description': (
                "Large tasks can seem intimidating and difficult. Instead of "
                "trying to tackle them all at once, try starting with a "
                "“tiny action.”"
            ),
            'more_info': (
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
            'description': (
                "Sometimes we let the little things prevent us from starting "
                "the tasks we want to do. Make activities more manageable by "
                "taking a “starter step.”"
            ),
            'more_info': (
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
            'description': (
                "We’ve picked some of the best tools and resources to help "
                "you succeed. Give them a try."
            ),
            'action_type': Action.RESOURCE,
        },
        Action.NOW: {
            'title': 'Do it now',
            'notification_text': 'Do it now',
            'description': (
                "When it comes to achieving your goals, there’s no time like "
                "the present. Consider performing this action right now, while "
                "it’s fresh on your mind."
            ),
            'action_type': Action.NOW,
        },
        Action.LATER: {
            'title': 'Do it later',
            'notification_text': 'Do it later',
            'description': (
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
            'source_link', 'source_notes', 'notes', 'icon', 'action_type',
        ]
        labels = {"notes": "Scratchpad"}

    class Media:
        js = (
            "foundation/js/vendor/jquery.js",
            "js/action_form.js",
        )


class BehaviorForm(forms.ModelForm):
    """A Form for creating/updating behaviors. This form orders related
    goals alphabetically."""
    goals = forms.ModelMultipleChoiceField(
        queryset=Goal.objects.all().order_by("title")
    )

    class Meta:
        model = Behavior
        fields = [
            'title', 'description', 'more_info', 'informal_list', 'notes',
            'external_resource', 'goals', 'icon', 'source_link', 'source_notes',
        ]
        labels = {"notes": "Scratchpad", 'informal_list': 'Action List'}


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
            'packaged_content', 'package_contributors', 'order', 'title',
            'description', 'icon', 'image', 'color', 'secondary_color', 'notes',
        ]
        labels = {"order": "Default Order", "notes": "Scratchpad"}
        widgets = {
            "color": forms.TextInput(attrs={'class': 'color-picker', 'type': 'color'}),
            "secondary_color": forms.TextInput(attrs={'class': 'color-picker', 'type': 'color'}),
        }

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        instance = kwargs.get('instance')
        initial_color = getattr(instance, 'color', '#2ECC71')
        secondary = getattr(instance, 'secondary_color', None)
        if 'secondary_color' not in initial and secondary is None:
            initial['secondary_color'] = colors.lighten(initial_color)
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)


class GoalForm(forms.ModelForm):
    """A Form for creating/updating goals. This form orders related categories
    alphabetically."""
    categories = forms.ModelMultipleChoiceField(queryset=Category.objects.all().order_by("title"))

    class Meta:
        model = Goal
        fields = [
            'categories', 'title', 'description', 'more_info', 'icon', 'notes',
        ]
        labels = {"notes": "Scratchpad"}


class ActionTriggerForm(forms.ModelForm):
    """A form for creating a default trigger while creating an action. The
    Trigger object returned by this form (e.g. when calling .save()) will:

    - have trigger_type = 'time'
    - an auto-generated hash as a name.

    """
    recurrences = RecurrenceField(
        help_text="Select the rules to define how this reminder should repeat."
    )

    class Meta:
        model = Trigger
        fields = ['time', 'trigger_date', 'recurrences']
        widgets = {
            "time": TimeSelectWidget(include_empty=True),
            "trigger_date": forms.TextInput(attrs={'class': 'datepicker'}),
        }
        labels = {
            "time": "Reminder Time",
            "trigger_date": "Reminder Date",
        }

    def save(self, *args, **kwargs):
        obj = super().save(*args, **kwargs)
        obj.trigger_type = "time"
        obj.name = date_hash()
        return obj


class TriggerForm(forms.ModelForm):
    recurrences = RecurrenceField(
        help_text="Select the rules to define how this reminder should repeat."
    )

    class Meta:
        model = Trigger
        fields = ['name', 'trigger_type', 'time', 'trigger_date', 'recurrences']
        widgets = {
            "time": TimeSelectWidget(),
            "trigger_date": forms.TextInput(attrs={'class': 'datepicker'}),
        }
        labels = {
            "time": "Reminder Time",
            "trigger_date": "Reminder Date",
        }


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
        queryset=Goal.objects.none(),
        help_text="Select the packages in which to enroll each person"
    )

    def __init__(self, category, *args, **kwargs):
        """Provice a specific category for this for in order to enroll users
        in it's set of Goals."""
        super().__init__(*args, **kwargs)
        qs = Goal.objects.published().filter(categories=category)
        self.fields['packaged_goals'].queryset = qs

    def clean_email_addresses(self):
        """Returns a list of email addresses."""
        content = self.cleaned_data['email_addresses']
        return [email for email in re.split(r"\s|,", content) if email.strip()]


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
            '<a href="/terms/" target="_blank">Terms of Service</a>'
            'and <a href="/privacy/">Privacy Notice</a>.'
        )
    )


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
