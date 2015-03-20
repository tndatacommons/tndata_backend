import random

from rest_framework import mixins, viewsets
from rest_framework.authentication import (
    SessionAuthentication,
    TokenAuthentication,
)
from rest_framework.response import Response

from . import models
from . import permissions
from . import serializers


class RandomQuestionViewSet(viewsets.ViewSet):
    """This endpoint retuns a single, random Question. The returned data
    may represent one of three different types of questions: Liker,
    Multiple Choice, or Open-Ended.

    The questions provided by this endpoint are guaranteed to not have been
    answered by the authenticated user.

    ## Question Types

    For details on the different question types, see their respective api docs:

    * [LikertQuestion](/api/survey/likert/)
    * [MultipleChoiceQuestion](/api/survey/multiplechoice/)
    * [OpenEndedQuestion](/api/survey/open/)

    ## Additional information

    This endpoint includes two pieces of additional information in its response:

    * `question_type` -- tells you the type of question returned, and will be
      on of "likertquestion", "multiplechoicequestion", or "openendedquestion"
    * `response_url` -- is the link to the endpoint to which response data
      should be POSTed.

    ----

    """
    questions = {
        models.LikertQuestion.__name__.lower(): {
            'model': models.LikertQuestion,
            'serializer': serializers.LikertQuestionSerializer,
            'related_response_name': 'likertresponse',
        },
        models.MultipleChoiceQuestion.__name__.lower(): {
            'model': models.MultipleChoiceQuestion,
            'serializer': serializers.MultipleChoiceQuestionSerializer,
            'related_response_name': 'multiplechoiceresponse',
        },
        models.OpenEndedQuestion.__name__.lower(): {
            'model': models.OpenEndedQuestion,
            'serializer': serializers.OpenEndedQuestionSerializer,
            'related_response_name': 'openendedresponse',
        }
    }

    def _get_random_question(self, user):
        questions = []
        # Find all the available questions that the user has not answered.
        for q in self.questions.values():
            kwargs = {"{0}__user".format(q['related_response_name']): user}
            questions.extend(list(q['model'].objects.available().exclude(**kwargs)))

        # Pick a random one.
        item = random.choice(questions)
        api_path = item.get_api_response_url()  # Grab the URI for the response.
        model_name = item.__class__.__name__.lower()  # remember which model

        # Serialize it.
        item = self.questions[model_name]['serializer']().to_native(item)
        item['question_type'] = model_name
        item['response_url'] = self.request.build_absolute_uri(api_path)
        return item

    def list(self, request):
        item = self._get_random_question(request.user)
        return Response(item)


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
