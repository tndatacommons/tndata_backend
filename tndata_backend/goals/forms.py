from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.utils.text import slugify

from utils.db import get_max_order

from . models import Action, Behavior, Category, Goal, Trigger
from . utils import read_uploaded_csv


class ActionForm(forms.ModelForm):
    """A Form for creating/updating actions. This form orders related behaviors
    alphabetically."""
    behavior = forms.ModelMultipleChoiceField(queryset=Behavior.objects.all().order_by("title"))

    class Meta:
        model = Action
        fields = [
            'sequence_order', 'behavior', 'title', 'source_link', 'source_notes',
            'notes', 'narrative_block', 'description', 'outcome',
            'external_resource', 'default_trigger', 'notification_text',
            'icon', 'image',
        ]


class BehaviorForm(forms.ModelForm):
    """A Form for creating/updating behaviors. This form orders related
    categories and goals alphabetically."""
    categories = forms.ModelMultipleChoiceField(queryset=Category.objects.all().order_by("title"))
    goals = forms.ModelMultipleChoiceField(queryset=Goal.objects.all().order_by("title"))

    class Meta:
        model = Behavior
        fields = [
            'title', 'source_link', 'source_notes', 'notes', 'narrative_block',
            'description', 'outcome', 'external_resource', 'informal_list',
            'categories', 'goals', 'icon', 'image',
        ]


class GoalForm(forms.ModelForm):
    """A Form for creating/updating goals. This form orders related categories
    alphabetically."""
    categories = forms.ModelMultipleChoiceField(queryset=Category.objects.all().order_by("title"))

    class Meta:
        model = Goal
        fields = [
            'categories', 'title', 'subtitle', 'description', 'outcome', 'icon',
        ]


class TriggerForm(forms.ModelForm):
    class Meta:
        model = Trigger
        fields = [
            'name', 'trigger_type', 'frequency', 'time', 'date', 'location',
            'text', 'instruction',
        ]
        widgets = {
            "time": forms.TimeInput(attrs={
                'class': 'timepicker',
                'type': 'time'
            }),
            "date": forms.DateInput(attrs={
                'class': 'datepicker',
                'type': 'date'
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
