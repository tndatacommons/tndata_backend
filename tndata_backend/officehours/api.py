from django.db.models import Q

from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import list_route
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
    """This endpoint will list the authenticated user's officehours.

    ## Menu
    - <a href="#retrieve-office-hours">Retrieve Office Hours</a>
    - <a href="#creating-office-hours">Create</a>
    - <a href="#alternative-post-format">Alternative POST formats</a>
    - <a href="#updating-a-officehours">Update</a>
    - <a href="#deleting-a-officehours">Delete</a>

    ## Retrieve Office Hours

    Send a GET request to retrieve the user's list of officehours. The result
    will contain an array of objects with the following data:

    - `id`: The OfficeHours's unique ID
    - `user`: The User ID for the user that created/owns the object.
    - `schedule`: a JSON blob representing the schedule hours during the week.
    - `updated_on`: Time at which the object was updated.
    - `created_on`: Time at which the object was created.
    - `expires_on`: The time at which the entry will expire


    ### Schedule format:

    A JSON object whose keys are days of the week, and whose values are
    2-tuples (arrays) of the start/ending times for set office hours;
    For example, `'DAY': [[from_time, to_time], ... ],`. The following is
    and example:

        {
            'Monday': [
                ["8:30", "10:30]
            ],
            'Friday': [
                ["15:30", "16:30],
                ["14:30", "15:00"]
            ]
        }

    ## Creating Office Hours

    As a teacher/faculty, you can send a POST request with the following
    information to create office hours:

        {
            'schedule':  ...
        }

    ### Alternative POST format

    You may condense the days on which office horus are available into a single
    string. It's format is: `SMTWRFZ HH:mm-HH:mm`, where `S` = Sunday,
    `M` = Monday, ..., `R` = Thursday, and `Z` = Saturday.

        {
            'meetingtime': 'MWF 11:30-13:30',
        }

    ## Updating a OfficeHours

    Send a PUT request with the fields you wish to update to
    `/api/officehours/ID/`.

    ## Deleting a OfficeHours

    Send a DELETE request to `/api/officehours/ID/`.

    ----

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

        # TODO: See: http://stackoverflow.com/a/18571508/182778
        # if 'user' not in request.data:
            # request.data['user'] = request.user.id
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)
        #request.data.update({'user': request.user.id})
        return super().update(request, *args, **kwargs)


class CourseViewSet(mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.UpdateModelMixin,
                    viewsets.GenericViewSet):
    """This endpoint will list the authenticated user's courses, whether they're
    a student or a teacher.

    ## Menu

    - <a href="#retrieve-a-course">Retrieve a course</a>
    - <a href="#creating-a-course">Create a course</a>
    - <a href="#alternative-post-format">Alterative POST formats</a>
    - <a href="#updating-a-course">Update</a>
    - <a href="#deleting-a-course">Delete</a>
    - <a href="#adding-a-student-to-a-course">Adding a student</a>

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
    - `meetingtime`: A string representing a condensed version of the meeting
      time and days for these office hours. e.g. `MWF 08:30-10:30`.
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

    ## Adding a student to a Course

    Send a POST request to `/api/courses/enroll/` with the following payload:

        {'code': "XYZ4" }

    This will retrieve the related Course and enroll the student in that course.

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsOwner]
    pagination_class = PageSizePagination

    def get_queryset(self):
        # This should include courses in which the authenticated user is a
        # STUDENT or a TEACHER.
        qs = super().get_queryset()
        qs = qs.filter(Q(user=self.request.user) | Q(students=self.request.user))
        self.queryset = qs.distinct()
        return self.queryset

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""
        if not request.user.is_authenticated():
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)
        request.data.update({'user': request.user.id})
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)
        request.data.update({'user': request.user.id})
        return super().update(request, *args, **kwargs)

    @list_route(methods=['post'], url_path='enroll')
    def enroll(self, request):
        """Ability for a student to enroll themselves in a course with a Code"""
        if not request.user.is_authenticated():
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)

        if request.method == "POST":
            try:
                course = self.queryset.get(code=request.data['code'])
                course.students.add(request.user)
                course.save()

                data = self.serializer_class(course).data
                return Response(data, status=status.HTTP_201_CREATED)
            except (IndexError, models.Course.DoesNotExist):
                return Response(
                    data={'error': "Specified Course not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
