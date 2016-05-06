from django.conf import settings
from rest_framework.serializers import ReadOnlyField


class ReadOnlyDatetimeField(ReadOnlyField):
    """This is a read-only field that properly formats datetime values."""

    def to_representation(self, value):
        try:
            # Ensure that we use the Specified Datetime formatting for the
            # next_reminder field.
            return value.strftime(settings.REST_FRAMEWORK['DATETIME_FORMAT'])
        except AttributeError:
            raise TypeError(
                "ReadOnlyDatetimeField is only usable with datetime objects")
