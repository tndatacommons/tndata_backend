from rest_framework import mixins, viewsets
from rest_framework.authentication import (
    SessionAuthentication,
    TokenAuthentication,
)

from . import models
from . import permissions
from . import serializers


class LikertQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """This is a read-only endpoint for all available Likert Questions.

    """
    queryset = models.LikertQuestion.objects.available()
    serializer_class = serializers.LikertQuestionSerializer


class MultipleChoiceQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """This is a read-only endpoint for all available Multiple Choice Questions.

    """
    queryset = models.MultipleChoiceQuestion.objects.available()
    serializer_class = serializers.MultipleChoiceQuestionSerializer


class OpenEndedQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """This is a read-only endpoint for all available Open-Ended Questions.

    """
    queryset = models.OpenEndedQuestion.objects.available()
    serializer_class = serializers.OpenEndedQuestionSerializer


class LikertResponseViewSet(mixins.CreateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    """This endpoint lists the [LikertQuestion](/api/survey/likert/)s to which
    a [User](/api/users/) has responded.

    GET requests to this page will list all questions belonging to the User.

    ## Adding a Response

    To save a User's response to a question, POST to this endpoint with the
    following data:

        {'question': QUESTION_ID, 'selected_option': VALUE}

    Where value is one of the given options for the question.

    ## Updating/Deleting a Response.

    Updating or deleting a response is currently not supported.

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.LikertResponse.objects.all()
    serializer_class = serializers.LikertResponseSerializer
    permission_classes = [permissions.IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""
        request.DATA['user'] = request.user.id
        return super(LikertResponseViewSet, self).create(request, *args, **kwargs)
