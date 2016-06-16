from django.conf import settings

from rest_framework import serializers
from rest_framework.fields import empty


class ReadOnlyDatetimeField(serializers.ReadOnlyField):
    """This is a read-only field that properly formats datetime values."""

    def to_representation(self, value):
        try:
            # Ensure that we use the Specified Datetime formatting for the
            # next_reminder field.
            return value.strftime(settings.REST_FRAMEWORK['DATETIME_FORMAT'])
        except AttributeError:
            raise TypeError(
                "ReadOnlyDatetimeField is only usable with datetime objects")


class EmptyFieldMixin:
    """Sets the following defaults:

    * allow_null = True
    * required = False

    And converts both None and '' values to `None` during serialization and
    deserialization.

    """
    def __init__(self, *args, **kwargs):
        """Sets the default values of `allow_null=True` and `required=False`"""
        kwargs['allow_null'] = kwargs.get('allow_null', True)
        kwargs['required'] = kwargs.get('required', False)
        super().__init__(*args, **kwargs)

    def to_internal_value(self, value):
        """When converting to an internal value, convert any '' to None."""
        if value == "" or value is None:
            return None
        return super().to_internal_value(value)

    def to_representation(self, value):
        if value == "" or value is None:
            return None
        return super().to_representation(value)


class NullableDateField(EmptyFieldMixin, serializers.DateField):
    """A Custom DateField that allows both None and Empty String values, and
    in both cases returns a `None` value.

    This class also sets default format and input format values:

    * format: YYYY-mm-dd
    * input formats: yyyy-mm-dd, yyyy/mm/dd, or ""

    """
    format = "%Y-%m-%d"
    input_formats = ["%Y-%m-%d", "%Y/%m/%d", ""]  # 2015-06-30, 2015/06/30


class NullableTimeField(EmptyFieldMixin, serializers.TimeField):
    """A Custom TimeField that allows both None and Empty String values, and
    in both cases returns a `None` value.

    This class also sets the default format and input format values:

    * format: HH:MM
    * input formats: HH:MM, HH:MM:ss, or ""

    """
    format = "%H:%M"
    input_formats = ["%H:%M", "%H:%M:%S", ""]  # 23:30, 23:30:45, or ''


class NullableCharField(EmptyFieldMixin, serializers.CharField):
    """A Custom CharField that allows both None and Empty String values
    initially, but converts both to a `None` value.

    """
    def run_validation(self, data=empty):
        if data in ['', None]:
            return None
        return super().run_validation(data=data)
