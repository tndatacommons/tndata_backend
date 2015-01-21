from django import forms
from . models import Action, Category, Interest, InterestGroup
from . utils import read_csv


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
                "{0} is not a CSV File".format(uploade_file.content_type)
            )
        content = read_csv(uploaded_file)
        return content

    def _contains_data(self, row):
        return any(col.strip() for col in row)

    def _get_type(self, row):
        try:
            row_type = row[0].lower().strip().replace(' ', '')
        except(IndexError, ValueError):
            row_type = None
        if row_type not in self.VALID_TYPES:
            raise self.InvalidFormat("File contains invalid data types")
        return row_type

    def _create_category(self, row):
        print(', '.join(row))  # TODO

    def _create_interest(self, row):
        print(', '.join(row))  # TODO

    def _create_interestgroup(self, row):
        print(', '.join(row))  # TODO

    def _create_action(self, row):
        print(', '.join(row))  # TODO

    def process_row(self, row):
        # A mapping between the row type and the method that should process it
        method_map = {
            'action': self._create_action,
            'category': self._create_category,
            'interest': self._create_interest,
            'interestgroup': self._create_interestgroup,
        }
        if self._contains_data(row):
            row_type = self._get_type(row)
            method_map[row_type](row)

    def save(self):
        """Once the form's `is_valid` method has been called, this method
        can read and parse the content from the uploaded file, returning
        a coherent dictionary.

        """
        for row in self._read_file():
            self.process_row(row)
