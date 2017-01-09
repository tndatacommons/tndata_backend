from django.contrib.auth import get_user_model
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
