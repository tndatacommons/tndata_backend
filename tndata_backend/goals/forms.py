import csv
from django import forms
from . models import InterestGroup


class InterestGroupSelectionForm(forms.Form):
    """This form allows a user to select multiple `InterestGroup`s.

    It is currently used to allow a user to assign a new/existing Interest
    to InterestGroups / Categories.
    """
    add_to_groups = forms.ModelMultipleChoiceField(
        queryset=InterestGroup.objects.all()
    )


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        help_text="Upload a CSV file to populate the content library"
    )

    def _read_file(self):
        lines = self.cleaned_data['csv_file'].readlines()
        content = [row.decode('utf8') for row in lines]
        return csv.reader(content)

    def get_data(self):
        """Once the form's `is_valid` method has been called, this method
        can read and parse the content from the uploaded file, returning
        a coherent dictionary.

        """
        result = {}
        for row in self._read_file():
            # TODO: remove this and do the real work.
            # e.g. know the format of the file, and organize into an appropriate
            # dict representation.
            print(", ".join(row))
        return result
        # TODO: once we have the dict, what should use it's data to generate
        # Category, Interest, Action data?
