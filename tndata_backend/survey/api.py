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
                            mixins.RetrieveModelMixin,
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

    ## Viewing the individual response

    Additionally, you can retrieve information for a single Response through
    the endpoint including it's ID: `/api/survey/likert/responses/{response_id}/`.

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


class OpenEndedResponseViewSet(mixins.CreateModelMixin,
                               mixins.ListModelMixin,
                               mixins.RetrieveModelMixin,
                               viewsets.GenericViewSet):
    """This endpoint lists the [OpenEndedQuestion](/api/survey/open/)s to
    which a [User](/api/users/) has responded.

    GET requests to this page will list all questions belonging to the User.

    ## Adding a Response

    To save a User's response to a question, POST to this endpoint with the
    following data:

        {'question': QUESTION_ID, 'response': "SOME TEXT"}

    ## Updating/Deleting a Response.

    Updating or deleting a response is currently not supported.

    ## Viewing the individual response

    Additionally, you can retrieve information for a single Response through
    the endpoint including it's ID: `/api/survey/openended/responses/{response_id}/`.

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.OpenEndedResponse.objects.all()
    serializer_class = serializers.OpenEndedResponseSerializer
    permission_classes = [permissions.IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""
        request.DATA['user'] = request.user.id
        return super(OpenEndedResponseViewSet, self).create(request, *args, **kwargs)


class MultipleChoiceResponseViewSet(mixins.CreateModelMixin,
                                    mixins.ListModelMixin,
                                    mixins.RetrieveModelMixin,
                                    viewsets.GenericViewSet):
    """This endpoint lists the [MultipleChoiceQuestion](/api/survey/likert/)s
    to which a [User](/api/users/) has responded.

    GET requests to this page will list all questions belonging to the User.

    ## Adding a Response

    To save a User's response to a question, POST to this endpoint with the
    following data:

        {'question': QUESTION_ID, 'selected_option': OPTION_ID}


    ## Updating/Deleting a Response.

    Updating or deleting a response is currently not supported.

    ## Viewing the individual response

    Additionally, you can retrieve information for a single Response through
    the endpoint including it's ID:
    `/api/survey/multiplechoice/responses/{response_id}/`.

    ----

    """
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    queryset = models.MultipleChoiceResponse.objects.all()
    serializer_class = serializers.MultipleChoiceResponseSerializer
    permission_classes = [permissions.IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user__id=self.request.user.id)

    def create(self, request, *args, **kwargs):
        """Only create objects for the authenticated user."""
        request.DATA['user'] = request.user.id
        return super(MultipleChoiceResponseViewSet, self).create(request, *args, **kwargs)
