from rest_framework import serializers
from utils.serializers import ObjectTypeModelSerializer

from . models import Course, OfficeHours


class OfficeHoursSerializer(ObjectTypeModelSerializer):
    class Meta:
        model = OfficeHours
        fields = (
            'id', 'user', 'from_time', 'to_time', 'days', 'expires_on',
            'updated_on', 'created_on',
        )
        read_only_fields = ("id", 'updated_on', "created_on")


class CourseSerializer(ObjectTypeModelSerializer):
    code = serializers.CharField(required=False)

    class Meta:
        model = Course
        fields = (
            'id', 'user', 'name', 'start_time', 'location', 'days',
            'code', 'students', 'expires_on', 'updated_on', 'created_on',
        )
        read_only_fields = ("id", 'updated_on', "created_on", 'students')

    def to_representation(self, obj):
        """Include a serialized Goal object in the result."""
        results = super().to_representation(obj)
        students = results.get('students', [])
        results['students'] = [
            {'id': student.id, 'name': student.get_full_name}
            for student in students
        ]
        return results
