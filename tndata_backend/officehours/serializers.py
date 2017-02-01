from collections import defaultdict
from datetime import time

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.fields import ListField
from utils.serializers import ObjectTypeModelSerializer

from . models import Course, OfficeHours


VALID_DAYS = {
    'S': 'Sunday',
    'M': 'Monday',
    'T': 'Tuesday',
    'W': 'Wednesday',
    'R': 'Thursday',
    'F': 'Friday',
    'Z': 'Saturday',
}


class WorkingListField(ListField):
    """A ListField subclass that correctly converts its data to a list"""
    def to_internal_value(self, data):
        """I don't know WTF I have to do this, but our ListField values
        are getting passed in as a nested list. So, this method hooks into
        the validation process to pull out the actual data that we want.

        E.G.:  [['Monday', 'Tuesday']] -> ['Monday', 'Tuesday']

        """
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            data = data[0]
        return super().to_internal_value(data)


class OfficeHoursSerializer(ObjectTypeModelSerializer):
    class Meta:
        model = OfficeHours
        fields = (
            'id', 'user', 'schedule', 'expires_on', 'updated_on', 'created_on',
        )
        read_only_fields = ("id", 'user', 'updated_on', "created_on")
        validators = []   # remove any default validators?

    def validate(self, data):
        """
        Handle the shortcut input format for combined days+start_time, e.g.
        the `MTWRFS H:mm-H:mm`-formatted input.

        """
        if 'meetingtime' in data:
            # Handle `MTWRFS H:mm-H:mm`-formatted input
            schedule = defaultdict(list)
            days, times = data['meetingtime'].split()
            days = [VALID_DAYS[x] for x in days]

            for day in days:
                start, end = times.split('-')
                schedule[day].append([start, end])
            data['schedule'] = dict(schedule)
        return data

    def is_valid(self, raise_exception=False):
        self.initial_data = self.validate(self.initial_data)
        return super().is_valid(raise_exception=raise_exception)


class CourseSerializer(ObjectTypeModelSerializer):
    code = serializers.CharField(required=False)
    days = WorkingListField()

    class Meta:
        model = Course
        fields = (
            'id', 'user', 'name', 'start_time', 'location', 'days',
            'meetingtime', 'code', 'students', 'expires_on',
            'updated_on', 'created_on',
        )
        read_only_fields = (
            "id", "user", 'updated_on', "created_on", 'students', 'meetingtime'
        )
        validators = []   # remove any default validators?

    def validate(self, data):
        """
        Handle the shortcut input format for combined days+start_time, e.g.
        the `MTWRFS H:mm-H:mm`-formatted input.

        """
        # Handle `MTWRFS H:mm-H:mm`-formatted input
        if 'meetingtime' in data:
            days, times = data['meetingtime'].split()

            data['days'] = [VALID_DAYS[x] for x in days]
            try:
                start, end = times.split('-')
            except ValueError:  # Assume we only got 1 time (not 2)
                start = times
            start_h, start_m = start.split(":")
            data['start_time'] = time(int(start_h), int(start_m))
            # TODO: end_time currently not supported.

        return data

    def is_valid(self, raise_exception=False):
        self.initial_data = self.validate(self.initial_data)
        return super().is_valid(raise_exception=raise_exception)

    def to_representation(self, obj):
        """Include a serialized student & faculty info."""
        User = get_user_model()
        results = super().to_representation(obj)
        student_ids = results.get('students', [])
        students = User.objects.filter(pk__in=student_ids)
        results['students'] = [
            {
                'id': student.id,
                'name': student.get_full_name(),
                'username': student.username,
                'avatar': student.userprofile.google_image,
            }
            for student in students
        ]
        user = User.objects.get(pk=results['user'])
        results['teacher'] = {
            'id': user.id,
            'name': user.get_full_name(),
            'username': user.username,
            'email': user.email,
            'avatar': user.userprofile.google_image,
        }
        return results
