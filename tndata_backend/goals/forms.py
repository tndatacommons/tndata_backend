from datetime import datetime
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.utils.text import slugify

from . models import Action, Category, Interest, InterestGroup
from . utils import get_max_order, read_uploaded_csv


class ActionForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = [
            'order', 'name', 'summary', 'description', 'interests',
            'default_reminder_time', 'default_reminder_frequency',
            'icon', 'notes', 'source_name', 'source_link',
        ]
        widgets = {
            "default_reminder_time": forms.TimeInput(attrs={'class': 'foo', 'type': 'time'}),
        }


class InterestGroupSelectionForm(forms.Form):
    """This form allows a user to select multiple `InterestGroup`s.

    It is currently used to allow a user to assign a new/existing Interest
    to InterestGroups / Categories.
    """
    add_to_groups = forms.ModelMultipleChoiceField(
        queryset=InterestGroup.objects.all()
    )

    def __init__(self, *args, **kwargs):
        # Grab some form-provided values for the `add_to_groups` field.
        qs = kwargs.pop('queryset', InterestGroup.objects.all())
        initial = kwargs.pop('initial', None)
        super(InterestGroupSelectionForm, self).__init__(*args, **kwargs)
        self.fields['add_to_groups'].queryset = qs
        self.fields['add_to_groups'].initial = initial


class InvalidFormatException(Exception):
    """Custom exception that gets raised when the CSVUploadForm fails."""
    pass


class CSVUploadForm(forms.Form):
    InvalidFormat = InvalidFormatException
    VALID_TYPES = ['action', 'category', 'interest', 'interestgroup']

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
        name = row[1]
        desc = row[2]
        try:
            # Update the description if this exists.
            category = Category.objects.get(name_slug=slugify(name))
            category.description = desc
            category.save()
        except Category.DoesNotExist:
            order = get_max_order(Category)
            Category.objects.create(order=order, name=name, description=desc)

    def _create_interest(self, row):
        name = row[1]
        desc = row[2]
        try:
            interest = Interest.objects.get(name_slug=slugify(name))
            interest.description = desc
            interest.save()
        except Interest.DoesNotExist:
            order = get_max_order(Interest)
            Interest.objects.create(order=order, name=name, description=desc)

    def _create_interestgroup(self, row):
        name = row[1]
        category = Category.objects.get(name_slug=slugify(row[2]))
        interest_names = [col.strip() for col in row[3:] if col.strip()]
        try:
            ig = InterestGroup.objects.get(name_slug=slugify(name))
            ig.category = category
            ig.name = name
            ig.save()
        except InterestGroup.DoesNotExist:
            ig = InterestGroup.objects.create(category=category, name=name)

        for iname in interest_names:
            # Retreive the interest and connect with the above group.
            # Assume they exist. if not, we'll fail/roll back the transaction
            interest = Interest.objects.get(name_slug=slugify(iname))
            ig.interests.add(interest)

    def _create_action(self, row):
        name, summary, desc, time, freq = row[1:6]
        freq = freq.strip().lower()
        time = datetime.strptime(time.strip(), "%H:%M")
        interest_names = [col.strip() for col in row[6:] if col.strip()]

        try:
            action = Action.objects.get(name_slug=slugify(name))
            action.summary = summary
            action.description = desc
            action.default_reminder_time = time.time()
            action.default_reminder_frequency = freq
            action.save()
        except Action.DoesNotExist:
            order = get_max_order(Action)
            action = Action.objects.create(
                order=order,
                name=name,
                summary=summary,
                description=desc,
                default_reminder_time=time.time(),
                default_reminder_frequency=freq
            )

        for iname in interest_names:
            # Retreive the interest and connect with the above action.
            # Assume they exist. if not, we'll fail/roll back the transaction
            interest = Interest.objects.get(name_slug=slugify(iname))
            action.interests.add(interest)

    def process_row(self, row):
        # A mapping between the row type and the method that should process it
        method_map = {
            'action': self._create_action,
            'category': self._create_category,
            'interest': self._create_interest,
            'interestgroup': self._create_interestgroup,
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
