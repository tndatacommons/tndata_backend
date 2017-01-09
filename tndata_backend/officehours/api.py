from datetime import time

from rest_framework import mixins, permissions, status, viewsets
from rest_framework.authentication import (
    SessionAuthentication, TokenAuthentication
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from . import models
from . serializers import OfficeHoursSerializer, CourseSerializer


class IsOwner(permissions.IsAuthenticated):
    """Only allow owners of an object to view/edit it."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class PageSizePagination(PageNumberPagination):
    """Allow specifying a `page_size` querystring param to change page size."""
    page_size_query_param = 'page_size'


class OfficeHoursViewSet(mixins.CreateModelMixin,
                         mixins.ListModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.DestroyModelMixin,
                         mixins.UpdateModelMixin,
                         viewsets.GenericViewSet):
    """ViewSet for OfficeHours.

    TODO: write docs.

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.OfficeHours.objects.all()
    serializer_class = OfficeHoursSerializer
    permission_classes = [IsOwner]
    pagination_class = PageSizePagination

    def get_queryset(self):
        self.queryset = super().get_queryset().filter(user=self.request.user)
        return self.queryset

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""
        if not request.user.is_authenticated():
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)
        request.data['user'] = request.user.id
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)
        request.data['user'] = request.user.id
        return super().update(request, *args, **kwargs)


class CourseViewSet(mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.UpdateModelMixin,
                    viewsets.GenericViewSet):
    """This endpoint will list the authenticated user's courses, whether they're
    a student or a teacher.

    ## Retrieve a Course

    Send a GET request to retrieve the user's list of coruses. A course object
    will contain the following data:

    - `id`: The Course's unique ID
    - `user`: The User ID for the user that created/owns the course (i.e. the
      teacher/faculty.
    - `name`: The name of the course.
    - `start_time`: Time at which the course starts.
    - `location`: The course's location
    - `days`: An array of strigns: The days on which the course meets.
    - `code`: The *share code* for the course.
    - `students`: An array of student information.
    - `updated_on`: Time at which the course was updated.
    - `created_on`: Time at which the course was created.
    - `expires_on`: The time at which the course entry will expire
    - `teacher`: An object with additional teacher details.

    ## Creating a Course

    As a teacher/faculty, you can send a POST request with the following
    information to create a course:

        {
            'name': 'COURSE NAME',
            'start_time': 'COURSE START TIME',
            'location': 'LOCATION',
            'days': ['Monday', 'Tuesday', 'Friday],
        }

    ### Alternative POST format

    You may condense the days & time of the course into a single string called
    `meetingtime`. It's format is: `SMTWRFZ HH:mm-HH:mm`, where `S` = Sunday,
    `M` = Monday, ..., `R` = Thursday, and `Z` = Saturday. The `HH:mm`
    represents hours and minutes.

        {
            'name': 'COURSE NAME',
            'meetingtime': 'MWF 11:30-13:30',
            'location': 'LOCATION',
        }

    ## Updating a Course

    Send a PUT request with the fields you wish to update to `/api/courses/ID/`.

    ## Deleting a Course

    Send a DELETE request to `/api/courses/ID/`.

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsOwner]
    pagination_class = PageSizePagination

    def get_queryset(self):
        self.queryset = super().get_queryset().filter(user=self.request.user)
        return self.queryset

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""
        if not request.user.is_authenticated():
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)

        payload = request.data.copy()
        payload['user'] = request.user.id

        valid_days = {
            'S': 'Sunday',
            'M': 'Monday',
            'T': 'Tuesday',
            'W': 'Wednesday',
            'R': 'Thursday',
            'F': 'Friday',
            'Z': 'Saturday',
        }
        # Handle `MTWRFS H:mm-H:mm`-formatted input
        if 'meetingtime' in payload:
            days, times = payload['meetingtime'].split()
            payload['days'] = [valid_days[x] for x in days]
            start, end = times.split('-')
            start_h, start_m = start.split(":")
            payload['start_time'] = time(int(start_h), int(start_m))

        request.data.update(payload)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)
        request.data['user'] = request.user.id
        return super().update(request, *args, **kwargs)
