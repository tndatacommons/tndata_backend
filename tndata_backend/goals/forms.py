from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.utils.text import slugify

from recurrence.forms import RecurrenceField
from utils.db import get_max_order
from utils import colors

from . models import Action, Behavior, Category, Goal, Trigger
from . utils import read_uploaded_csv


class ActionForm(forms.ModelForm):
    """A Form for creating/updating actions. This form orders related behaviors
    alphabetically."""
    behavior = forms.ModelChoiceField(queryset=Behavior.objects.all().order_by("title"))

    class Meta:
        model = Action
        fields = [
            'sequence_order', 'behavior', 'title', 'description',
            'more_info', 'external_resource', 'default_trigger',
            'notification_text', 'source_link', 'source_notes', 'notes',

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
    default_trigger = forms.ModelChoiceField(
        queryset=Trigger.objects.default(),
        required=False
    )

    def __init__(self, *args, **kwargs):
        default = Trigger.objects.default().get(
            name_slug='default-behavior-reminder'
        )
        instance = kwargs.get('instance', None)
        if instance and instance.default_trigger is None:
            kwargs['instance'].default_trigger = default
        elif 'initial' in kwargs and kwargs.get('initial') is None:
            kwargs['intitial'].update({'default_trigger': default})
        super().__init__(*args, **kwargs)

    class Meta:
        model = Behavior
        fields = [
            'title', 'description', 'more_info', 'informal_list',
            'external_resource', 'goals', 'icon', 'default_trigger',
            'source_link', 'source_notes',
            'notes',
        ]
        labels = {"notes": "Scratchpad", 'informal_list': 'Action List'}


class CategoryForm(forms.ModelForm):
    """A Form for creating/updateing Categories. This form customizes the widget
    for the color field."""

    class Meta:
        model = Category
        fields = [
            'order', 'title', 'description', 'icon', 'image', 'color',
            'secondary_color', 'notes',
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
            'categories', 'title', 'description', 'icon', 'notes',
        ]
        labels = {"notes": "Scratchpad"}


class TriggerForm(forms.ModelForm):
    recurrences = RecurrenceField()

    class Meta:
        model = Trigger
        fields = ['name', 'trigger_type', 'time', 'recurrences']
        widgets = {
            "time": forms.TimeInput(attrs={
                'class': 'timepicker',
                'type': 'time'
            }),
        }


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
