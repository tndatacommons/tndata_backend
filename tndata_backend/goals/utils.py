import csv
from django.db.models import Max
from io import TextIOWrapper


def get_max_order(model):
    """Given an instance of a Model class, query the largest existing value
    for the `order` field and add one. This is useful for pre-populated
    Category, Interest, and Action fields.

    """
    result = model.objects.aggregate(Max('order'))
    current_num = result['order__max'] or 0
    return current_num + 1


def read_uploaded_csv(uploaded_file, encoding='utf-8', errors='ignore'):
    """This is a generator that takes an uploaded file (such as an instance of
    InMemoryUploadedFile.file), converts it to a string (instead of bytes)
    representation, then parses it as a CSV.

    Returns a list of lists containing strings, and removes any empty rows.

    NOTES:

    1. This makes a big assumption about utf-8 encodings, and the errors
       param means we potentially lose data!
    2. InMemoryUploadedFileSee: http://stackoverflow.com/a/16243182/182778

    """
    file = TextIOWrapper(
        uploaded_file.file,
        encoding=encoding,
        newline='',
        errors=errors
    )
    for row in csv.reader(file):
        if any(row):
            yield row
